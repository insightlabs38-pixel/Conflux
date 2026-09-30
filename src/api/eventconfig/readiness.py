"""Event readiness (PD-F001-B01): the one list of what is missing before an event can launch.

Every rule is code over rows the domain already owns; nothing is stored and no rule re-validates
what `Event.clean` or a serializer already enforces. The dashboard's `configuration_checks` and the
operations launch checklist are projections of this list, so they can no longer disagree. A rule of
a module that is off contributes nothing (`modules.is_enabled`), and every unresolved item says
where to fix it. Readiness is advisory: it informs `draft -> open` (the open transition records what
was unresolved) but only `Event.clean` blocks it.
"""

from collections.abc import Callable
from dataclasses import dataclass

from community.models import VotingPlan
from eligibility.models import EligibilityRules
from evaluations.models import EvaluationPlan, EvaluationPoolStrategy
from events.models import RegistrationInviteCode, RegistrationMode
from forms.models import FormDefinition
from policies.models import TemporalGate

from . import modules


@dataclass(frozen=True)
class Rule:
    id: str
    severity: str  # "blocker" | "warning"
    module: str  # "core" or an optional module key: a module that is off contributes no rule
    check: Callable  # event -> (passed, detail)
    destination: str  # where an organizer fixes it
    section: str = ""  # the tab inside that destination
    # What the dashboard's legacy `configuration_checks` list says for this rule, if it is one.
    legacy_check: bool = False


def _window_outside_event(event, opens_at, closes_at):
    if not event.starts_at or not event.ends_at:
        return False
    if closes_at and closes_at <= event.starts_at:
        return True
    if opens_at and opens_at >= event.ends_at:
        return True
    return False


def _event_dates(event):
    passed = bool(event.starts_at and event.ends_at)
    return (
        passed,
        "Start and end dates are set." if passed else "Set the event start and end dates.",
    )


def _forms_published(event):
    unpublished = [
        form.name
        for form in FormDefinition.objects.filter(event=event)
        if form.versions.order_by("-number").first() is None
    ]
    if not unpublished:
        return True, "All forms have a published version."
    return False, f"Publish a version for: {', '.join(unpublished)}."


def _gate_windows(event):
    contradictory = [
        gate.name
        for gate in TemporalGate.objects.filter(event=event)
        if _window_outside_event(event, gate.opens_at, gate.closes_at)
    ]
    if not contradictory:
        return True, "No gate windows fall outside the event dates."
    return False, f"Gate window entirely outside event dates: {', '.join(contradictory)}."


def _voting_window(event):
    plan = VotingPlan.objects.filter(event=event).first()
    if plan is None:
        return True, "No community voting configured."
    if not _window_outside_event(event, plan.opens_at, plan.closes_at):
        return True, "Voting window overlaps the event dates."
    return False, "Community voting window is entirely outside the event dates."


def _judging_rubrics(event):
    missing = [
        plan.name
        for plan in EvaluationPlan.objects.filter(stage__event=event)
        if plan.current_rubric_version is None
    ]
    if not missing:
        return True, "Every evaluation plan has a published rubric."
    return False, f"Publish a rubric for: {', '.join(missing)}."


def _judging_pools(event):
    unstaffed = [
        plan.name
        for plan in EvaluationPlan.objects.filter(stage__event=event).select_related("pool")
        if plan.pool_strategy
        in (EvaluationPoolStrategy.ALL_JUDGES, EvaluationPoolStrategy.ASSIGNED_SUBSET)
        and (plan.pool_id is None or not plan.pool.memberships.exists())
    ]
    if not unstaffed:
        return True, "Every evaluation plan has a staffed judge pool."
    return False, f"No judges assigned for: {', '.join(unstaffed)}."


def _public_page(event):
    if not event.is_public:
        return True, "Event is not public yet."
    page = getattr(event, "page", None)
    if page is not None and page.blocks.exists():
        return True, "Public page has content."
    return False, "Event is public but its page has no content blocks."


def _tracks(event):
    # Tracks are optional; it only matters when a rule asks every project to pick one.
    rules = EligibilityRules.objects.filter(event=event).first()
    if not (rules and rules.require_track):
        return True, "No track is required."
    if event.tracks.exists():
        return True, "Tracks are defined for the track requirement."
    return False, "Projects must pick a track but the event has none: add a track."


def _registration_invites(event):
    settings = getattr(event, "registration_settings", None)
    if settings is None or settings.mode != RegistrationMode.INVITE_ONLY:
        return True, "Registration does not need invite codes."
    codes = RegistrationInviteCode.objects.filter(event=event, revoked_at__isnull=True)
    if any(code.is_valid() for code in codes):
        return True, "Invite codes are available."
    return False, "Registration is invite-only but no usable invite code exists."


RULES = [
    Rule("event_dates", "blocker", "core", _event_dates, "setup", "settings", legacy_check=True),
    Rule("tracks", "blocker", "core", _tracks, "setup", "settings", legacy_check=True),
    Rule("forms_published", "blocker", "core", _forms_published, "setup", "forms"),
    Rule("gate_windows", "warning", "core", _gate_windows, "setup", "policies"),
    Rule(
        "voting_window",
        "warning",
        "community_voting",
        _voting_window,
        "judging",
        "CommunityVotingBuilder",
    ),
    Rule("judging_rubrics", "blocker", "core", _judging_rubrics, "judging", "EvaluationBuilder"),
    Rule("judging_pools", "warning", "core", _judging_pools, "judging", "EvaluationBuilder"),
    Rule("public_page", "warning", "core", _public_page, "setup", "page"),
    Rule(
        "registration_invites",
        "warning",
        "core",
        _registration_invites,
        "participants",
        "RegistrationPanel",
    ),
]
RULE_IDS = [rule.id for rule in RULES]
_LEGACY_IDS = {rule.id for rule in RULES if rule.legacy_check}


def compute_readiness(event) -> dict:
    items = []
    for rule in RULES:
        if rule.module != "core" and not modules.is_enabled(event, rule.module):
            continue
        passed, detail = rule.check(event)
        items.append(
            {
                "id": rule.id,
                "severity": rule.severity,
                "passed": passed,
                "detail": detail,
                "module": rule.module,
                "fix": {"destination": rule.destination, "section": rule.section},
            }
        )
    blocked = any(not i["passed"] and i["severity"] == "blocker" for i in items)
    warned = any(not i["passed"] and i["severity"] == "warning" for i in items)
    return {
        "status": "blocked" if blocked else "warning" if warned else "ready",
        "items": items,
    }


def unresolved(readiness) -> dict:
    """The ids still open, for audit and for the open transition's response."""
    return {
        severity: [i["id"] for i in readiness["items"] if not i["passed"] and i["severity"] == sev]
        for severity, sev in (("blockers", "blocker"), ("warnings", "warning"))
    }


def configuration_checks(readiness) -> list[str]:
    """The dashboard's legacy list: what is unresolved among the rules it always reported."""
    return [i["detail"] for i in readiness["items"] if i["id"] in _LEGACY_IDS and not i["passed"]]
