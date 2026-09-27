from datetime import datetime

import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

CRITERIA = [
    {"id": "impact", "name": "Impact", "weight": 2, "min_score": 0, "max_score": 10},
]


def cookie_client(token):
    client = Client()
    client.cookies["session"] = token
    return client


def make_fixture():
    organizer = User.objects.create_user(username="organizer", password="unused")
    participant = User.objects.create_user(username="member", password="unused")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=participant, workspace=workspace, role=Role.PARTICIPANT)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    return workspace, event, organizer, participant


def history_url(workspace, event):
    return f"/api/v1/audit/{workspace.public_id}/events/{event.public_id}/config-history/"


def event_url(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"


def stages_url(workspace, event, suffix=""):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/stages/{suffix}"


def gates_url(workspace, event, suffix=""):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/temporal-gates/{suffix}"
    )


def plans_url(workspace, event, stage, suffix=""):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/{suffix}"
    )


def test_event_settings_change_is_readable_as_a_before_after_diff():
    workspace, event, organizer, _ = make_fixture()
    client = cookie_client(Session.issue(organizer).token)

    client.patch(
        event_url(workspace, event),
        {"name": "Hack 2.0", "timezone": "America/New_York"},
        content_type="application/json",
    )

    entries = client.get(history_url(workspace, event)).json()
    assert len(entries) == 1
    entry = entries[0]
    assert entry["action"] == "event.updated"
    assert entry["resource_type"] == "Event"
    assert entry["changes"]["name"] == {"before": "Hack", "after": "Hack 2.0"}
    assert entry["changes"]["timezone"] == {"before": "UTC", "after": "America/New_York"}


def test_stage_update_diff_and_a_no_op_patch_records_nothing():
    workspace, event, organizer, _ = make_fixture()
    client = cookie_client(Session.issue(organizer).token)
    stage_id = client.post(stages_url(workspace, event), {"name": "Finals"}).json()["public_id"]

    client.patch(
        stages_url(workspace, event, f"{stage_id}/"),
        {"name": "Finals"},
        content_type="application/json",
    )
    assert client.get(history_url(workspace, event)).json() == []

    client.patch(
        stages_url(workspace, event, f"{stage_id}/"),
        {"name": "Grand Finals"},
        content_type="application/json",
    )
    entries = client.get(history_url(workspace, event)).json()
    assert len(entries) == 1
    assert entries[0]["action"] == "stage.updated"
    assert entries[0]["changes"] == {"name": {"before": "Finals", "after": "Grand Finals"}}


def test_temporal_gate_update_diff_uses_isoformat_datetimes():
    workspace, event, organizer, _ = make_fixture()
    client = cookie_client(Session.issue(organizer).token)
    gate_id = client.post(
        gates_url(workspace, event),
        {"name": "Submissions", "opens_at": "2026-01-01T00:00:00Z"},
        content_type="application/json",
    ).json()["public_id"]

    client.patch(
        gates_url(workspace, event, f"{gate_id}/"),
        {"opens_at": "2026-02-01T00:00:00Z"},
        content_type="application/json",
    )

    entries = client.get(history_url(workspace, event)).json()
    assert len(entries) == 1
    change = entries[0]["changes"]["opens_at"]
    # Compare instants, not raw strings: DRF renders the datetime in the
    # server's configured local offset, not necessarily "Z".
    assert datetime.fromisoformat(change["before"]) == datetime.fromisoformat(
        "2026-01-01T00:00:00+00:00"
    )
    assert datetime.fromisoformat(change["after"]) == datetime.fromisoformat(
        "2026-02-01T00:00:00+00:00"
    )


def test_rubric_publish_diffs_criteria_against_the_prior_version():
    workspace, event, organizer, _ = make_fixture()
    stage = Stage.objects.create(event=event, name="Finals")
    client = cookie_client(Session.issue(organizer).token)
    plan_id = client.post(
        plans_url(workspace, event, stage),
        data={"name": "Panel", "draft_criteria": CRITERIA},
        content_type="application/json",
    ).json()["public_id"]

    first_published = client.post(
        plans_url(workspace, event, stage, f"{plan_id}/publish-rubric/")
    ).json()
    first_entries = client.get(history_url(workspace, event)).json()
    assert len(first_entries) == 1
    assert first_entries[0]["action"] == "rubric.published"
    assert first_entries[0]["changes"]["criteria"]["before"] is None
    assert first_entries[0]["changes"]["criteria"]["after"] == first_published["criteria"]

    new_criteria = CRITERIA + [
        {"id": "polish", "name": "Polish", "weight": 1, "min_score": 0, "max_score": 10}
    ]
    client.patch(
        plans_url(workspace, event, stage, f"{plan_id}/"),
        {"draft_criteria": new_criteria},
        content_type="application/json",
    )
    second_published = client.post(
        plans_url(workspace, event, stage, f"{plan_id}/publish-rubric/")
    ).json()

    entries = client.get(history_url(workspace, event)).json()
    assert len(entries) == 2
    assert entries[0]["changes"]["criteria"]["before"] == first_published["criteria"]
    assert entries[0]["changes"]["criteria"]["after"] == second_published["criteria"]


def test_creation_and_deletion_rows_are_omitted_since_they_carry_no_diff():
    workspace, event, organizer, _ = make_fixture()
    client = cookie_client(Session.issue(organizer).token)
    stage_id = client.post(stages_url(workspace, event), {"name": "Finals"}).json()["public_id"]
    client.delete(stages_url(workspace, event, f"{stage_id}/"))

    assert client.get(history_url(workspace, event)).json() == []


def test_history_is_scoped_to_its_own_event_and_ordered_newest_first():
    workspace, event, organizer, _ = make_fixture()
    other_event = Event.objects.create(workspace=workspace, name="Other", slug="other")
    client = cookie_client(Session.issue(organizer).token)

    client.patch(
        event_url(workspace, other_event), {"name": "Other 2.0"}, content_type="application/json"
    )
    client.patch(event_url(workspace, event), {"name": "Hack A"}, content_type="application/json")
    client.patch(event_url(workspace, event), {"name": "Hack B"}, content_type="application/json")

    entries = client.get(history_url(workspace, event)).json()
    assert [e["changes"]["name"]["after"] for e in entries] == ["Hack B", "Hack A"]


def test_participant_and_anonymous_cannot_read_config_history():
    workspace, event, organizer, participant = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    organizer_client.patch(
        event_url(workspace, event), {"name": "Hack A"}, content_type="application/json"
    )

    participant_client = cookie_client(Session.issue(participant).token)
    assert participant_client.get(history_url(workspace, event)).status_code == 403
    assert Client().get(history_url(workspace, event)).status_code in (401, 403)
