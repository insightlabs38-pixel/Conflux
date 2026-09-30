"""PD-F001-B01-T00 census: how today's persisted events and library presets map onto the contract.

Read-only. Run: docker compose exec -T app python manage.py shell < docs/verification/PD-F001-B01/probe_census.py
Library presets are instantiated inside a transaction that is rolled back.
"""

from collections import Counter

from django.db import transaction

from communications.checklist import compute_launch_checklist
from community.models import VotingPlan
from deliberation.models import DeliberationRoom
from eligibility.models import EligibilityRules
from events.models import Event, EventRegistrationSettings
from integrations.models import EventRetentionPolicy, WebhookSubscription
from eventconfig.presets import PRESETS
from integrations.template_library import instantiate_library_template
from mentorship.models import MentorProfile
from onsite.models import AgendaSession, Location
from presentation.models import Page
from workspaces.models import Workspace

# Optional-module evidence: the real probes of eventconfig.modules ("has content for the event").
from eventconfig.modules import MODULES as OPTIONAL_MODULES  # noqa: E402

MODULES = {
    key: (lambda e, module=module: module.has_content(Event.objects.filter(pk=e.pk)))
    for key, module in OPTIONAL_MODULES.items()
}


def configuration_checks(event):  # verbatim copy of EventDashboardView's rules
    out = []
    if not event.starts_at or not event.ends_at:
        out.append("dates")
    if not event.tracks.exists():
        out.append("track")
    if not event.base_prizes.exists():
        out.append("base_prize")
    return out


def describe(event):
    checklist = compute_launch_checklist(event)
    failing = [i["id"] for i in checklist["items"] if not i["passed"]]
    return {
        "event": event.slug,
        "status": event.status,
        "modules_in_use": sorted(k for k, probe in MODULES.items() if probe(event)),
        "registration_settings_row": EventRegistrationSettings.objects.filter(event=event).exists(),
        "dashboard_configuration_checks": configuration_checks(event),
        "launch_checklist": checklist["status"],
        "launch_checklist_failing": failing,
        "two_readiness_sources_agree": (not configuration_checks(event)) == (checklist["status"] != "blocked"),
    }


print("== persisted events")
rows = [describe(e) for e in Event.objects.all().order_by("pk")]
for row in rows:
    print(row)
print("events:", len(rows))
print("disagreeing readiness sources:", sum(not r["two_readiness_sources_agree"] for r in rows))
print("module usage:", dict(Counter(m for r in rows for m in r["modules_in_use"])))

print("== library presets instantiated on an empty draft (rolled back)")
workspace = Workspace.objects.first()
try:
    with transaction.atomic():
        for slug in PRESETS:
            event = instantiate_library_template(
                workspace=workspace,
                template_slug=slug,
                name=f"census {slug}",
                slug=f"census-{slug}",
                actor=None,
            )
            print(slug, describe(event))
            print("   registration settings row:", EventRegistrationSettings.objects.filter(event=event).exists(),
                  "| tracks:", list(event.tracks.values_list("name", flat=True)),
                  "| base prizes:", event.base_prizes.count(), "| dates:", bool(event.starts_at))
        raise RuntimeError("rollback")
except RuntimeError:
    pass
print("events after rollback:", Event.objects.count())
