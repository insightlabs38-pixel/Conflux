"""Optional modules of an event (PD-F001-B01): which parts of the platform this event uses.

A module is enabled when an organizer switched it on **or** it already has content for the event, so
nothing with data ever disappears and a legacy event with no settings behaves as before. Disabling
never deletes anything and is refused while the module has content. The catalog and the "has
content" probes are code; the only stored state is `EventModuleSetting`. Enablement decides what is
offered (navigation, collapsed panels, readiness rules); it is never authorization, every endpoint
keeps its own permission checks.
"""

from collections.abc import Callable
from dataclasses import dataclass

from community.models import VotingPlan
from django.core.exceptions import ValidationError
from eligibility.models import EligibilityFinding, EligibilityReview, EligibilityRules
from events.models import Event
from governance.models import DeadlineExceptionRequest
from integrations.models import (
    EventRetentionPolicy,
    ExternalQualifierBinding,
    ExternalQualifierImport,
    WebhookSubscription,
)
from mentorship.models import MentorProfile, MentorRequest, OfficeHourSlot
from onsite.models import AgendaSession, Attendance, Location
from presentation.models import Page

from .models import EventModuleSetting


@dataclass(frozen=True)
class Module:
    key: str
    label: str
    description: str
    # The organizer navigation destination this module owns, if it is a whole destination.
    destination: str | None
    # True when the module has content for any event in the queryset.
    has_content: Callable[..., bool]
    # Extra workspace-level content (e.g. webhooks not bound to one event); union view only.
    has_workspace_content: Callable[..., bool] | None = None
    # Where the module's tools live: (destination, tab), so a turned-on module can be opened.
    home: tuple[str, str] = ("", "")


def _any(model, events, **filters):
    return model.objects.filter(event__in=events, **filters).exists()


MODULES = {
    module.key: module
    for module in (
        Module(
            "eligibility_review",
            "Eligibility review",
            "Review projects against your rules, track findings and decide deadline exceptions.",
            "eligibility",
            lambda events: EligibilityReview.objects.filter(project__event__in=events).exists()
            or EligibilityFinding.objects.filter(review__project__event__in=events).exists()
            or _any(EligibilityRules, events, require_clearance=True)
            # The destination also hosts deadline-exception decisions: a request must be reachable.
            or _any(DeadlineExceptionRequest, events),
            home=("eligibility", ""),
        ),
        Module(
            "onsite",
            "On-site",
            "Locations, agenda, check-in and project placement for in-person events.",
            "onsite",
            lambda events: _any(Location, events)
            or _any(AgendaSession, events)
            or _any(Attendance, events),
            home=("onsite", ""),
        ),
        Module(
            "integrations",
            "Integrations",
            "Webhooks, external qualifiers, retention and data portability.",
            "integrations",
            lambda events: _any(WebhookSubscription, events)
            or _any(EventRetentionPolicy, events)
            or _any(ExternalQualifierBinding, events)
            or _any(ExternalQualifierImport, events),
            lambda workspace: WebhookSubscription.objects.filter(
                workspace=workspace, event__isnull=True
            ).exists(),
            home=("integrations", ""),
        ),
        Module(
            "community_voting",
            "Community voting",
            "Let the community vote on projects alongside judges.",
            None,
            lambda events: VotingPlan.objects.filter(event__in=events).exists(),
            home=("judging", "CommunityVotingBuilder"),
        ),
        Module(
            "mentorship",
            "Mentorship",
            "Mentors, office hours and mentor requests.",
            None,
            lambda events: _any(MentorProfile, events)
            or _any(MentorRequest, events)
            or _any(OfficeHourSlot, events),
            home=("participants", "MentorDeskPanel"),
        ),
        Module(
            "public_page",
            "Public event page",
            "Build the page participants and visitors see.",
            None,
            lambda events: Page.objects.filter(event__in=events).exists(),
            home=("setup", "page"),
        ),
    )
}


def _events(event):
    return Event.objects.filter(pk=event.pk)


def _in_use_reason(module, scope_label):
    return f"{module.label} already has content {scope_label}; remove it before turning it off."


def _entry(module, *, in_use, explicit, scope_label):
    enabled = in_use or explicit is True
    return {
        "key": module.key,
        "label": module.label,
        "description": module.description,
        "destination": module.destination,
        "home": {"destination": module.home[0], "section": module.home[1]},
        "enabled": enabled,
        "in_use": in_use,
        "explicit": explicit,
        "can_disable": enabled and not in_use,
        "reason": (_in_use_reason(module, scope_label) if in_use else ""),
    }


def event_modules(event):
    """Effective state of every optional module for one event."""
    events = _events(event)
    explicit = {s.module: s.enabled for s in event.module_settings.all()}
    return [
        _entry(
            module,
            in_use=module.has_content(events),
            explicit=explicit.get(module.key),
            scope_label="for this event",
        )
        for module in MODULES.values()
    ]


def workspace_modules(workspace):
    """Union across the workspace's events: a module is offered if any event uses or enabled it."""
    events = Event.objects.filter(workspace=workspace)
    enabled = set(
        EventModuleSetting.objects.filter(event__in=events, enabled=True).values_list(
            "module", flat=True
        )
    )
    out = []
    for module in MODULES.values():
        in_use = module.has_content(events) or bool(
            module.has_workspace_content and module.has_workspace_content(workspace)
        )
        out.append(
            _entry(
                module,
                in_use=in_use,
                explicit=True if module.key in enabled else None,
                scope_label="in this workspace",
            )
        )
    return out


def is_enabled(event, key):
    """Whether a module is effective for the event; anything that is not a module is core (on)."""
    module = MODULES.get(key)
    if module is None:
        return True
    setting = event.module_settings.filter(module=key).first()
    return module.has_content(_events(event)) or bool(setting and setting.enabled)


def set_enabled(event, key, enabled, *, actor):
    module = MODULES.get(key)
    if module is None:
        raise ValidationError({"module": "Unknown module."})
    if not enabled and module.has_content(_events(event)):
        raise ValidationError({"module": _in_use_reason(module, "for this event")})
    setting, _ = EventModuleSetting.objects.update_or_create(
        event=event, module=key, defaults={"enabled": enabled, "changed_by": actor}
    )
    return setting
