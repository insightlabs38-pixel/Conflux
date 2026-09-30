"""PD-F001-B01-T05: one readiness list; the legacy surfaces are projections of it."""

from datetime import UTC, datetime, timedelta

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from communications.checklist import compute_launch_checklist
from community.models import VotingPlan
from django.test import Client
from django.utils import timezone
from eligibility.models import EligibilityRules
from eventconfig.models import EventModuleSetting
from eventconfig.readiness import RULE_IDS, compute_readiness, unresolved
from events.models import (
    Event,
    EventRegistrationSettings,
    EventStatus,
    RegistrationInviteCode,
    RegistrationMode,
)
from forms.models import FormDefinition
from presentation.models import Page
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def setup():
    organizer = User.objects.create_user(username="org", password="unused")
    judge = User.objects.create_user(username="jdg", password="unused")
    workspace = Workspace.objects.create(name="Ready", slug="ready")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    now = timezone.now()
    event = Event.objects.create(
        workspace=workspace,
        name="E",
        slug="e",
        starts_at=now + timedelta(days=1),
        ends_at=now + timedelta(days=2),
    )
    return workspace, event, organizer, client_for(organizer), client_for(judge)


def api(workspace, event, path):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/{path}"


def item(readiness, item_id):
    return next((i for i in readiness["items"] if i["id"] == item_id), None)


def test_a_complete_minimal_event_has_nothing_unresolved_and_every_item_says_where_to_fix():
    _, event, *_ = setup()
    readiness = compute_readiness(event)
    assert readiness["status"] == "ready"
    assert [i["id"] for i in readiness["items"]] == [r for r in RULE_IDS if r != "voting_window"]
    assert all(i["fix"]["destination"] for i in readiness["items"])
    assert unresolved(readiness) == {"blockers": [], "warnings": []}


def test_each_rule_fails_and_recovers_with_a_useful_message():
    workspace, event, *_ = setup()
    # Dates
    event.starts_at = event.ends_at = None
    event.save()
    bad = item(compute_readiness(event), "event_dates")
    assert not bad["passed"] and bad["detail"] == "Set the event start and end dates."
    assert bad["fix"] == {"destination": "setup", "section": "settings"}

    # Tracks are optional unless projects are required to pick one.
    rules = EligibilityRules.objects.create(event=event, require_track=True)
    bad = item(compute_readiness(event), "tracks")
    assert not bad["passed"] and "add a track" in bad["detail"]
    event.tracks.create(name="AI")
    assert item(compute_readiness(event), "tracks")["passed"]
    rules.delete()

    # Unpublished form
    FormDefinition.objects.create(event=event, name="Application")
    bad = item(compute_readiness(event), "forms_published")
    assert not bad["passed"] and "Application" in bad["detail"]
    assert bad["fix"]["section"] == "forms"

    # Public without a page
    event.is_public = True
    event.save()
    assert not item(compute_readiness(event), "public_page")["passed"]
    Page.objects.create(event=event)
    assert not item(compute_readiness(event), "public_page")["passed"]  # still no blocks


def test_registration_invites_only_matter_for_invite_only_events():
    workspace, event, organizer, *_ = setup()
    assert item(compute_readiness(event), "registration_invites")["passed"]
    EventRegistrationSettings.objects.create(event=event, mode=RegistrationMode.INVITE_ONLY)
    bad = item(compute_readiness(event), "registration_invites")
    assert not bad["passed"] and bad["fix"]["destination"] == "participants"
    code = RegistrationInviteCode.objects.create(event=event, created_by=organizer)
    assert item(compute_readiness(event), "registration_invites")["passed"]
    code.revoked_at = datetime.now(UTC)
    code.save()
    assert not item(compute_readiness(event), "registration_invites")["passed"]


def test_a_disabled_module_contributes_no_rule_and_an_enabled_one_does():
    workspace, event, organizer, *_ = setup()
    assert item(compute_readiness(event), "voting_window") is None
    EventModuleSetting.objects.create(event=event, module="community_voting", enabled=True)
    assert item(compute_readiness(event), "voting_window")[
        "passed"
    ]  # on, no plan yet: nothing to check
    now = timezone.now()
    VotingPlan.objects.create(
        event=event, opens_at=now - timedelta(days=30), closes_at=now - timedelta(days=29)
    )
    bad = item(compute_readiness(event), "voting_window")
    assert not bad["passed"] and bad["module"] == "community_voting"


def test_the_legacy_surfaces_are_projections_and_agree_with_the_canonical_list():
    workspace, event, organizer, client, _ = setup()
    canonical = client.get(api(workspace, event, "readiness/")).json()
    legacy = client.get(api(workspace, event, "operations/checklist/")).json()
    assert legacy == canonical == compute_launch_checklist(event)
    dashboard = client.get(api(workspace, event, "dashboard/")).json()
    assert dashboard["configuration_checks"] == []

    event.starts_at = event.ends_at = None
    event.save()
    dashboard = client.get(api(workspace, event, "dashboard/")).json()
    assert dashboard["configuration_checks"] == ["Set the event start and end dates."]
    canonical = client.get(api(workspace, event, "readiness/")).json()
    assert canonical["status"] == "blocked"
    # Operator console health comes from the same list.
    console = client.get(f"/api/v1/workspaces/{workspace.public_id}/operator-console/").json()
    row = next(r for r in console["events"] if r["public_id"] == str(event.public_id))
    assert row["health"] == canonical["status"]
    assert row["blocker_count"] == len(unresolved(canonical)["blockers"])


def test_opening_is_advisory_but_records_what_was_unresolved():
    workspace, event, organizer, client, _ = setup()
    FormDefinition.objects.create(event=event, name="Unpublished")  # a blocker
    response = client.post(
        api(workspace, event, "status/"), data={"status": "open"}, content_type="application/json"
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["status"] == EventStatus.OPEN
    assert body["readiness"]["status"] == "blocked"
    audit = AuditEvent.objects.get(action="event.status_changed")
    assert audit.metadata["unresolved"]["blockers"] == ["forms_published"]
    # Later transitions carry no readiness.
    closed = client.post(
        api(workspace, event, "status/"), data={"status": "closed"}, content_type="application/json"
    )
    assert "readiness" not in closed.json()


def test_readiness_is_organizer_only_and_tenant_scoped():
    workspace, event, organizer, client, judge = setup()
    url = api(workspace, event, "readiness/")
    assert judge.get(url).status_code == 403
    assert Client().get(url).status_code in (401, 403)
    other = Workspace.objects.create(name="Other", slug="other")
    stranger = User.objects.create_user(username="str", password="unused")
    Membership.objects.create(user=stranger, workspace=other, role=Role.ORGANIZER)
    outsider = client_for(stranger)
    assert outsider.get(url).status_code == 403
    cross = f"/api/v1/workspaces/{other.public_id}/events/{event.public_id}/readiness/"
    assert outsider.get(cross).status_code == 404


def test_the_public_page_fix_points_at_features_until_the_module_is_on():
    workspace, event, *_ = setup()
    event.is_public = True
    event.save()
    bad = item(compute_readiness(event), "public_page")
    assert not bad["passed"] and "turn on the public event page" in bad["detail"]
    assert bad["fix"] == {"destination": "setup", "section": "features"}
    EventModuleSetting.objects.create(event=event, module="public_page", enabled=True)
    bad = item(compute_readiness(event), "public_page")
    assert "no content blocks" in bad["detail"]
    assert bad["fix"] == {"destination": "setup", "section": "page"}
