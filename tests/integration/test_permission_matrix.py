import pytest
from accounts.models import Session, User
from core.permission_matrix import build_permission_matrix
from django.test import Client
from events.models import Event
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client(user):
    result = Client()
    result.cookies["session"] = Session.issue(user).token
    return result


def by_view(matrix, view_name):
    return {entry["method"]: entry for entry in matrix if entry["view"] == view_name}


def test_matrix_reflects_every_registered_view_with_no_unrecognized_permission():
    matrix = build_permission_matrix()
    assert len(matrix) > 100
    assert all(not entry["unrecognized"] for entry in matrix)


def test_matrix_distinguishes_a_get_permissions_override_by_method():
    matrix = build_permission_matrix()
    track = by_view(matrix, "TrackListView")
    assert set(track["GET"]["roles"]) == {
        "participant",
        "judge",
        "organizer",
        "admin",
        "mentor",
        "volunteer",
        "sponsor",
    }
    assert track["POST"]["access"] == "roles"
    assert set(track["POST"]["roles"]) == {"organizer", "admin"}


def test_matrix_recognizes_any_authenticated_and_public_access():
    matrix = build_permission_matrix()
    my_application = by_view(matrix, "MyEventApplicationView")
    assert my_application["GET"]["access"] == "any_authenticated"
    assert my_application["POST"]["access"] == "any_authenticated"

    public_event = by_view(matrix, "PublicEventView")
    assert public_event["GET"]["access"] == "public"


def test_permission_matrix_endpoint_is_organizer_only():
    workspace = Workspace.objects.create(name="One", slug="one")
    organizer = User.objects.create_user(username="organizer")
    participant = User.objects.create_user(username="participant")
    Membership.objects.create(workspace=workspace, user=organizer, role=Role.ORGANIZER)
    Membership.objects.create(workspace=workspace, user=participant, role=Role.PARTICIPANT)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    url = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/permission-matrix/"

    assert client(participant).get(url).status_code == 403
    response = client(organizer).get(url)
    assert response.status_code == 200
    body = response.json()
    assert any(entry["view"] == "TrackListView" for entry in body)
