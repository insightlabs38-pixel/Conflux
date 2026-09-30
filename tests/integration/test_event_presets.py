"""PD-F001-B01-T03: a preset yields real defaults, not placeholders the organizer must clean up."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from communications.checklist import compute_launch_checklist
from django.test import Client
from eligibility.models import EligibilityRules
from eventconfig.models import EventProfile
from eventconfig.presets import PRESETS
from events.models import Event, EventRegistrationSettings, RegistrationMode
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

START = datetime(2027, 3, 5, 9, 0, tzinfo=UTC)
BERLIN = ZoneInfo("Europe/Berlin")


def setup():
    owner = User.objects.create_user(username="owner", password="unused")
    workspace = Workspace.objects.create(name="Presets", slug="presets")
    Membership.objects.create(user=owner, workspace=workspace, role=Role.ORGANIZER)
    client = Client()
    client.cookies["session"] = Session.issue(owner).token
    base = f"/api/v1/workspaces/{workspace.public_id}/event-templates/library/"
    return workspace, client, base


def create(client, base, key, **body):
    payload = {"name": "Spring", "slug": "spring", **body}
    return client.post(base + f"{key}/instantiate/", data=payload, content_type="application/json")


@pytest.mark.parametrize("key", list(PRESETS))
def test_preset_event_is_complete_except_what_only_the_organizer_knows(key):
    workspace, client, base = setup()
    preset = PRESETS[key]
    response = create(client, base, key, starts_at=START.isoformat(), timezone="Europe/Berlin")
    assert response.status_code == 201, response.content
    event = Event.objects.get(workspace=workspace, slug="spring")

    # Dates: the end is derived from the format's duration; the zone is the organizer's.
    assert event.starts_at == START
    assert event.ends_at == (START.astimezone(BERLIN) + preset.duration).astimezone(UTC)
    assert event.timezone == "Europe/Berlin"
    # Base decisions exist as real rows with the format's values.
    registration = EventRegistrationSettings.objects.get(event=event)
    assert registration.mode == preset.registration_mode
    rules = EligibilityRules.objects.get(event=event)
    assert (rules.min_team_size, rules.max_team_size) == (
        preset.min_team_size,
        preset.max_team_size,
    )
    assert rules.required_artifact_kinds == [str(k) for k in preset.required_artifact_kinds]
    profile = EventProfile.objects.get(event=event)
    assert (profile.preset_key, profile.preset_version) == (key, preset.version)

    # Launch readiness: nothing left to clean up except the judges only the organizer can name.
    checklist = compute_launch_checklist(event)
    failing = {item["id"] for item in checklist["items"] if not item["passed"]}
    assert failing == {"judging_pools"}
    assert checklist["status"] == "warning"

    # Audit: creation records the preset version; every published rubric is audited.
    created = AuditEvent.objects.get(action="event_template.library_instantiated")
    assert created.workspace == workspace
    rubric_audits = AuditEvent.objects.filter(action="rubric.published")
    assert rubric_audits.count() == len(preset.judging_stages)
    assert all(a.metadata["preset"] == key for a in rubric_audits)


def test_end_keeps_local_wall_clock_across_a_dst_change():
    workspace, client, base = setup()
    # 28-day grant from Fri 2027-03-05 10:00 Berlin; clocks go forward on 2027-03-28.
    response = create(client, base, "grant", starts_at=START.isoformat(), timezone="Europe/Berlin")
    assert response.status_code == 201, response.content
    event = Event.objects.get(workspace=workspace)
    assert event.ends_at == datetime(2027, 4, 2, 8, 0, tzinfo=UTC)  # 10:00 CEST, not 09:00
    assert event.ends_at.astimezone(BERLIN).hour == event.starts_at.astimezone(BERLIN).hour


def test_without_dates_the_only_blocker_is_the_dates():
    workspace, client, base = setup()
    assert create(client, base, "hackathon").status_code == 201
    event = Event.objects.get(workspace=workspace)
    checklist = compute_launch_checklist(event)
    blockers = {
        i["id"] for i in checklist["items"] if not i["passed"] and i["severity"] == "blocker"
    }
    assert blockers == {"event_dates"}
    assert event.starts_at is None and event.ends_at is None


def test_organizer_decisions_override_the_format_values():
    workspace, client, base = setup()
    response = create(
        client,
        base,
        "hackathon",
        registration_mode=RegistrationMode.INVITE_ONLY,
        min_team_size=2,
        max_team_size=3,
    )
    assert response.status_code == 201, response.content
    event = Event.objects.get(workspace=workspace)
    assert event.registration_settings.mode == RegistrationMode.INVITE_ONLY
    rules = event.eligibility_rules
    assert (rules.min_team_size, rules.max_team_size) == (2, 3)


@pytest.mark.parametrize(
    "body",
    [
        {"timezone": "Mars/Olympus"},
        {"registration_mode": "whoever"},
        {"min_team_size": 6, "max_team_size": 2},
    ],
)
def test_invalid_decisions_are_rejected_and_leave_nothing_behind(body):
    workspace, client, base = setup()
    response = create(client, base, "hackathon", **body)
    assert response.status_code == 400, response.content
    assert Event.objects.filter(workspace=workspace).count() == 0
    assert EventProfile.objects.count() == 0
    assert AuditEvent.objects.filter(workspace=workspace).count() == 0


def test_a_failed_creation_rolls_back_the_rubric_and_its_audit():
    workspace, client, base = setup()
    assert create(client, base, "hackathon").status_code == 201
    audits = AuditEvent.objects.count()
    # Same slug: the duplicate fails after nothing else has been written or audited.
    assert create(client, base, "hackathon").status_code == 400
    assert AuditEvent.objects.count() == audits
    assert Event.objects.filter(workspace=workspace).count() == 1


def test_library_listing_describes_the_real_defaults():
    _, client, base = setup()
    listed = {entry["slug"]: entry for entry in client.get(base).json()}
    assert set(listed) == set(PRESETS)
    for key, entry in listed.items():
        preset = PRESETS[key]
        assert entry["version"] == preset.version
        assert entry["duration_days"] == preset.duration_days
        assert entry["registration_mode"] == preset.registration_mode
        assert entry["criteria"] == [c.name for c in preset.criteria]
        assert entry["min_team_size"] <= entry["max_team_size"]


def test_presets_are_well_formed():
    for preset in PRESETS.values():
        assert preset.version >= 1
        assert preset.duration >= timedelta(hours=1)
        assert all(0 <= i < len(preset.stages) for i in preset.judging_stages)
        assert sum(c.weight for c in preset.criteria) > 0
        assert preset.min_team_size <= preset.max_team_size
