import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


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


def plan_url(workspace, event, suffix=""):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/voting-plan/{suffix}"


def test_organizer_can_read_and_configure_the_lazily_created_plan():
    workspace, event, organizer, _ = make_fixture()
    client = cookie_client(Session.issue(organizer).token)

    fetched = client.get(plan_url(workspace, event))
    assert fetched.status_code == 200
    assert fetched.json()["identity_mode"] == "authenticated"

    updated = client.patch(
        plan_url(workspace, event),
        {"identity_mode": "token", "comment_visibility": "organizer"},
        content_type="application/json",
    )
    assert updated.status_code == 200
    assert updated.json()["identity_mode"] == "token"


def test_organizer_can_issue_a_batch_of_vote_tokens():
    workspace, event, organizer, _ = make_fixture()
    client = cookie_client(Session.issue(organizer).token)
    client.get(plan_url(workspace, event))  # lazily creates the plan

    issued = client.post(
        plan_url(workspace, event, "tokens/"), {"count": 5}, content_type="application/json"
    )
    assert issued.status_code == 201
    assert len(issued.json()) == 5
    tokens = {t["token"] for t in issued.json()}
    assert len(tokens) == 5  # every token is unique

    listed = client.get(plan_url(workspace, event, "tokens/")).json()
    assert len(listed) == 5


def test_plan_configuration_is_organizer_only():
    workspace, event, _, participant = make_fixture()
    client = cookie_client(Session.issue(participant).token)
    assert client.get(plan_url(workspace, event)).status_code == 403
    assert (
        client.post(
            plan_url(workspace, event, "tokens/"), {"count": 1}, content_type="application/json"
        ).status_code
        == 403
    )


def test_plan_rejects_a_closing_time_before_opening_time():
    workspace, event, organizer, _ = make_fixture()
    client = cookie_client(Session.issue(organizer).token)
    client.get(plan_url(workspace, event))
    response = client.patch(
        plan_url(workspace, event),
        {"opens_at": "2026-06-02T00:00:00Z", "closes_at": "2026-06-01T00:00:00Z"},
        content_type="application/json",
    )
    assert response.status_code == 400
