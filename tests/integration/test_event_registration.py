import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event, EventStatus, RegistrationMode
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client(user):
    result = Client()
    result.cookies["session"] = Session.issue(user).token
    return result


def fixture(**event_kwargs):
    workspace = Workspace.objects.create(name="One", slug="one")
    organizer = User.objects.create_user(username="organizer")
    Membership.objects.create(workspace=workspace, user=organizer, role=Role.ORGANIZER)
    defaults = {
        "status": EventStatus.OPEN,
        "starts_at": "2027-01-01T00:00:00Z",
        "ends_at": "2027-01-02T00:00:00Z",
    }
    defaults.update(event_kwargs)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack", **defaults)
    return workspace, organizer, event


def base_url(workspace, event, suffix=""):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/{suffix}"


def new_user(username):
    return User.objects.create_user(username=username)


def test_open_registration_grants_membership_immediately():
    workspace, organizer, event = fixture()
    alice = new_user("alice")
    response = client(alice).post(
        base_url(workspace, event, "my-application/"), {}, content_type="application/json"
    )
    assert response.status_code == 201
    assert response.json()["status"] == "approved"
    assert Membership.objects.filter(
        workspace=workspace, user=alice, role=Role.PARTICIPANT
    ).exists()

    my = client(alice).get(base_url(workspace, event, "my-application/"))
    assert my.json()["application"]["status"] == "approved"

    duplicate = client(alice).post(
        base_url(workspace, event, "my-application/"), {}, content_type="application/json"
    )
    assert duplicate.status_code == 400


def test_registration_closed_outside_open_status():
    workspace, organizer, event = fixture(status=EventStatus.DRAFT, starts_at=None, ends_at=None)
    alice = new_user("alice")
    response = client(alice).post(
        base_url(workspace, event, "my-application/"), {}, content_type="application/json"
    )
    assert response.status_code == 400


def test_application_mode_requires_organizer_decision():
    workspace, organizer, event = fixture()
    organizer_client = client(organizer)
    settings_url = base_url(workspace, event, "registration-settings/")
    assert (
        organizer_client.put(
            settings_url, {"mode": "application"}, content_type="application/json"
        ).status_code
        == 200
    )

    alice = new_user("alice")
    applied = client(alice).post(
        base_url(workspace, event, "my-application/"),
        {"note": "Please let me in"},
        content_type="application/json",
    )
    assert applied.status_code == 201
    assert applied.json()["status"] == "pending"
    assert not Membership.objects.filter(workspace=workspace, user=alice).exists()

    applications = organizer_client.get(base_url(workspace, event, "applications/")).json()
    assert len(applications) == 1
    app_id = applications[0]["public_id"]
    assert client(alice).get(base_url(workspace, event, "applications/")).status_code == 403

    decide_url = base_url(workspace, event, f"applications/{app_id}/decide/")
    decided = organizer_client.post(
        decide_url, {"decision": "approved"}, content_type="application/json"
    )
    assert decided.status_code == 200
    assert decided.json()["status"] == "approved"
    assert Membership.objects.filter(
        workspace=workspace, user=alice, role=Role.PARTICIPANT
    ).exists()

    redecide = organizer_client.post(
        decide_url, {"decision": "rejected"}, content_type="application/json"
    )
    assert redecide.status_code == 400


def test_capacity_and_waitlist_gate_open_registration():
    workspace, organizer, event = fixture()
    organizer_client = client(organizer)
    settings_url = base_url(workspace, event, "registration-settings/")
    assert (
        organizer_client.put(
            settings_url,
            {"capacity": 1, "waitlist_enabled": True},
            content_type="application/json",
        ).status_code
        == 200
    )

    alice, bob = new_user("alice"), new_user("bob")
    first = client(alice).post(
        base_url(workspace, event, "my-application/"), {}, content_type="application/json"
    )
    assert first.json()["status"] == "approved"
    second = client(bob).post(
        base_url(workspace, event, "my-application/"), {}, content_type="application/json"
    )
    assert second.status_code == 201
    assert second.json()["status"] == "waitlisted"
    assert second.json()["waitlist_position"] == 1
    assert not Membership.objects.filter(workspace=workspace, user=bob).exists()

    assert (
        organizer_client.put(
            settings_url, {"waitlist_enabled": False}, content_type="application/json"
        ).status_code
        == 200
    )
    carol = new_user("carol")
    third = client(carol).post(
        base_url(workspace, event, "my-application/"), {}, content_type="application/json"
    )
    assert third.status_code == 400


def test_invite_only_registration_requires_a_valid_unspent_code():
    workspace, organizer, event = fixture()
    organizer_client = client(organizer)
    settings_url = base_url(workspace, event, "registration-settings/")
    organizer_client.put(
        settings_url, {"mode": RegistrationMode.INVITE_ONLY}, content_type="application/json"
    )

    alice = new_user("alice")
    missing_code = client(alice).post(
        base_url(workspace, event, "my-application/"), {}, content_type="application/json"
    )
    assert missing_code.status_code == 400

    created = organizer_client.post(
        base_url(workspace, event, "registration-invite-codes/"),
        {"max_uses": 1},
        content_type="application/json",
    )
    assert created.status_code == 201
    code = created.json()["code"]

    wrong_code = client(alice).post(
        base_url(workspace, event, "my-application/"),
        {"code": "not-a-real-code"},
        content_type="application/json",
    )
    assert wrong_code.status_code == 400

    approved = client(alice).post(
        base_url(workspace, event, "my-application/"),
        {"code": code},
        content_type="application/json",
    )
    assert approved.status_code == 201
    assert approved.json()["status"] == "approved"

    bob = new_user("bob")
    spent = client(bob).post(
        base_url(workspace, event, "my-application/"),
        {"code": code},
        content_type="application/json",
    )
    assert spent.status_code == 400

    codes = organizer_client.get(base_url(workspace, event, "registration-invite-codes/")).json()
    assert codes[0]["use_count"] == 1

    revoke = organizer_client.delete(
        base_url(workspace, event, f"registration-invite-codes/{codes[0]['public_id']}/")
    )
    assert revoke.status_code == 204
