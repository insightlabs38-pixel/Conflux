import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
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


def base_url(workspace, event, suffix):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/{suffix}"


def test_preset_list_is_available_to_an_organizer():
    workspace, event, organizer = make_event_with_organizer()
    response = cookie_client(issue(organizer)).get(base_url(workspace, event, "policy-presets/"))
    assert response.status_code == 200
    assert "organizers_only" in response.json()


def test_creating_a_policy_from_a_preset_needs_no_raw_json():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(issue(organizer))

    created = client.post(
        base_url(workspace, event, "policies/"),
        {"name": "Organizers gate", "preset": "organizers_only"},
        content_type="application/json",
    )
    assert created.status_code == 201
    assert created.json()["ast"] == {"op": "eq", "fact": "role", "value": "organizer"}


def test_a_preset_missing_its_required_param_is_rejected():
    workspace, event, organizer = make_event_with_organizer()
    response = cookie_client(issue(organizer)).post(
        base_url(workspace, event, "policies/"),
        {"name": "Window gate", "preset": "window_open"},
        content_type="application/json",
    )
    assert response.status_code == 400


def test_creating_a_policy_with_raw_ast_still_works():
    workspace, event, organizer = make_event_with_organizer()
    response = cookie_client(issue(organizer)).post(
        base_url(workspace, event, "policies/"),
        {"name": "Custom", "ast": {"op": "true"}},
        content_type="application/json",
    )
    assert response.status_code == 201


def test_binding_a_policy_to_an_action_and_listing_it():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(issue(organizer))
    policy = client.post(
        base_url(workspace, event, "policies/"),
        {"name": "Organizers gate", "preset": "organizers_only"},
        content_type="application/json",
    ).json()

    bound = client.post(
        base_url(workspace, event, "policy-bindings/"),
        {"action": "submit", "policy": policy["public_id"]},
        content_type="application/json",
    )
    assert bound.status_code == 201
    listed = client.get(base_url(workspace, event, "policy-bindings/"))
    assert listed.json()[0]["policy"] == policy["public_id"]


def test_creating_and_updating_a_temporal_gate():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(issue(organizer))
    created = client.post(
        base_url(workspace, event, "temporal-gates/"),
        {"name": "submissions"},
        content_type="application/json",
    )
    assert created.status_code == 201
    gate_id = created.json()["public_id"]

    updated = client.patch(
        base_url(workspace, event, f"temporal-gates/{gate_id}/"),
        {"closes_at": "2099-01-01T00:00:00Z"},
        content_type="application/json",
    )
    assert updated.status_code == 200
    assert updated.json()["closes_at"] is not None


def test_creating_an_exception_grant():
    workspace, event, organizer = make_event_with_organizer()
    response = cookie_client(issue(organizer)).post(
        base_url(workspace, event, "exception-grants/"),
        {
            "action": "submit",
            "subject_type": "team",
            "subject_id": "tm_01",
            "reason": "Approved late entry.",
        },
        content_type="application/json",
    )
    assert response.status_code == 201
    assert response.json()["reason"] == "Approved late entry."


def test_non_organizer_is_blocked_from_all_policy_endpoints():
    workspace, event, _organizer = make_event_with_organizer()
    participant = make_user("participant")
    Membership.objects.create(user=participant, workspace=workspace, role=Role.PARTICIPANT)
    client = cookie_client(issue(participant))

    assert client.get(base_url(workspace, event, "policy-presets/")).status_code in (401, 403)
    assert client.get(base_url(workspace, event, "policies/")).status_code in (401, 403)
    assert client.get(base_url(workspace, event, "temporal-gates/")).status_code in (401, 403)
