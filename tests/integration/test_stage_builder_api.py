import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
from stages.models import Stage, StageEntry
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def make_user(username):
    return User.objects.create_user(username=username, password="unused")


def cookie_client(token):
    client = Client()
    client.cookies["session"] = token
    return client


def issue(user):
    return Session.issue(user).token


def make_event_with_organizer():
    organizer = make_user("organizer")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    return workspace, event, organizer


def stage_url(workspace, event, suffix=""):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/stages/{suffix}"


def transition_url(workspace, event, suffix=""):
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
    return f"{base}/stage-transitions/{suffix}"


def graph_validate_url(workspace, event):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/stage-graph/validate/"
    )


def evidence_url(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/stage-evidence/"


def advance_url(workspace, event, stage):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"
        f"stages/{stage.public_id}/advance/"
    )


# --- Stages CRUD --------------------------------------------------------


def test_organizer_can_create_list_and_update_a_stage():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(issue(organizer))

    created = client.post(
        stage_url(workspace, event),
        {"name": "Submission", "is_initial": True},
        content_type="application/json",
    )
    assert created.status_code == 201
    stage_id = created.json()["public_id"]

    listed = client.get(stage_url(workspace, event))
    assert listed.status_code == 200
    assert [s["name"] for s in listed.json()] == ["Submission"]

    updated = client.patch(
        stage_url(workspace, event, f"{stage_id}/"),
        {"position": 5},
        content_type="application/json",
    )
    assert updated.status_code == 200
    assert updated.json()["position"] == 5


def test_non_organizer_cannot_create_a_stage():
    workspace, event, _organizer = make_event_with_organizer()
    participant = make_user("participant")
    Membership.objects.create(user=participant, workspace=workspace, role=Role.PARTICIPANT)

    response = cookie_client(issue(participant)).post(
        stage_url(workspace, event), {"name": "Submission"}, content_type="application/json"
    )
    assert response.status_code in (401, 403)


def test_duplicate_stage_name_in_the_same_event_is_rejected():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(issue(organizer))
    client.post(
        stage_url(workspace, event), {"name": "Submission"}, content_type="application/json"
    )

    response = client.post(
        stage_url(workspace, event), {"name": "Submission"}, content_type="application/json"
    )
    assert response.status_code == 400


def test_a_stage_that_has_ever_held_a_participant_cannot_be_deleted():
    workspace, event, organizer = make_event_with_organizer()
    stage = Stage.objects.create(event=event, name="Submission")
    StageEntry.objects.enter(stage, "team", "tm_01")

    response = cookie_client(issue(organizer)).delete(
        stage_url(workspace, event, f"{stage.public_id}/")
    )
    assert response.status_code == 400


# --- Transitions ---------------------------------------------------------


def test_creating_a_transition_and_rejecting_a_cycle():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(issue(organizer))
    a = Stage.objects.create(event=event, name="A", is_initial=True)
    b = Stage.objects.create(event=event, name="B")

    forward = client.post(
        transition_url(workspace, event),
        {"from_stage": str(a.public_id), "to_stage": str(b.public_id)},
        content_type="application/json",
    )
    assert forward.status_code == 201

    backward = client.post(
        transition_url(workspace, event),
        {"from_stage": str(b.public_id), "to_stage": str(a.public_id)},
        content_type="application/json",
    )
    assert backward.status_code == 400


def test_deleting_a_transition():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(issue(organizer))
    a = Stage.objects.create(event=event, name="A", is_initial=True)
    b = Stage.objects.create(event=event, name="B")
    created = client.post(
        transition_url(workspace, event),
        {"from_stage": str(a.public_id), "to_stage": str(b.public_id)},
        content_type="application/json",
    )
    transition_id = created.json()["public_id"]

    response = client.delete(transition_url(workspace, event, f"{transition_id}/"))
    assert response.status_code == 204
    assert client.get(transition_url(workspace, event)).json() == []


# --- Graph validation ------------------------------------------------------


def test_graph_validation_reports_valid_and_invalid():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(issue(organizer))
    Stage.objects.create(event=event, name="Orphan")  # no initial stage yet

    invalid = client.get(graph_validate_url(workspace, event))
    assert invalid.json()["valid"] is False

    Stage.objects.filter(event=event, name="Orphan").update(is_initial=True)
    valid = client.get(graph_validate_url(workspace, event))
    assert valid.json() == {"valid": True, "order": [str(Stage.objects.get().public_id)]}


# --- Advancement + evidence -------------------------------------------------


def test_advance_endpoint_moves_a_subject_and_evidence_shows_it():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(issue(organizer))
    submission = Stage.objects.create(event=event, name="Submission", is_initial=True)
    judging = Stage.objects.create(event=event, name="Judging")
    client.post(
        transition_url(workspace, event),
        {"from_stage": str(submission.public_id), "to_stage": str(judging.public_id)},
        content_type="application/json",
    )
    StageEntry.objects.enter(submission, "team", "tm_01")

    response = client.post(
        advance_url(workspace, event, submission),
        {
            "to_stage": str(judging.public_id),
            "strategy": "everyone",
            "candidates": [{"subject_type": "team", "subject_id": "tm_01"}],
        },
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["advanced"] == [{"subject_type": "team", "subject_id": "tm_01"}]

    evidence = client.get(evidence_url(workspace, event))
    assert evidence.status_code == 200
    assert evidence.json()[0]["metadata"]["strategy"] == "everyone"


def test_available_strategies_are_listed():
    workspace, event, organizer = make_event_with_organizer()
    stage = Stage.objects.create(event=event, name="Submission", is_initial=True)
    response = cookie_client(issue(organizer)).get(advance_url(workspace, event, stage))
    assert "everyone" in response.json()["strategies"]
    assert "top_n" in response.json()["strategies"]
