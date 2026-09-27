import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event, Track
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


def tracks_url(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/tracks/"


def test_organizer_can_list_and_create_tracks():
    workspace, event, organizer, _ = make_fixture()
    client = cookie_client(Session.issue(organizer).token)
    created = client.post(
        tracks_url(workspace, event), {"name": "AI"}, content_type="application/json"
    )
    assert created.status_code == 201
    assert [t["name"] for t in client.get(tracks_url(workspace, event)).json()] == ["AI"]


def test_participant_can_read_tracks_so_they_can_pick_one_for_a_project_but_not_create_one():
    workspace, event, _, participant = make_fixture()
    Track.objects.create(event=event, name="AI")
    client = cookie_client(Session.issue(participant).token)
    assert [t["name"] for t in client.get(tracks_url(workspace, event)).json()] == ["AI"]
    denied = client.post(
        tracks_url(workspace, event), {"name": "Fintech"}, content_type="application/json"
    )
    assert denied.status_code == 403


def test_anonymous_cannot_read_or_create_tracks():
    workspace, event, _, _ = make_fixture()
    client = Client()
    assert client.get(tracks_url(workspace, event)).status_code in (401, 403)
    assert client.post(
        tracks_url(workspace, event), {"name": "AI"}, content_type="application/json"
    ).status_code in (401, 403)
