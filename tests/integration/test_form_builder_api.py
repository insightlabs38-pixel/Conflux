import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def setup_clients():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    clients = {}
    for role in (Role.ORGANIZER, Role.PARTICIPANT):
        user = User.objects.create_user(username=role, password="unused")
        Membership.objects.create(workspace=workspace, user=user, role=role)
        client = Client()
        client.cookies["session"] = Session.issue(user).token
        clients[role] = client
    return event, clients


def test_organizer_creates_edits_previews_and_publishes_form_versions():
    event, clients = setup_clients()
    base = f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}/forms/"
    organizer = clients[Role.ORGANIZER]
    created = organizer.post(base, {"name": "Application"}, content_type="application/json")
    assert created.status_code == 201
    detail = base + created.json()["public_id"] + "/"
    schema = {"fields": [{"id": "pitch", "type": "text", "label": "Pitch", "required": True}]}
    assert (
        organizer.put(detail, {"schema": schema}, content_type="application/json").status_code
        == 200
    )
    published = organizer.post(detail + "publish/")
    assert published.status_code == 201
    assert published.json()["number"] == 1
    assert published.json()["schema"] == schema
    assert organizer.get(detail + "versions/").json()[0]["schema"] == schema
    assert organizer.get(base).json()[0]["draft_schema"] == schema
    assert clients[Role.PARTICIPANT].get(base).status_code in (401, 403)


def test_invalid_schema_does_not_publish_and_archived_event_rejects_edits():
    event, clients = setup_clients()
    base = f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}/forms/"
    organizer = clients[Role.ORGANIZER]
    created = organizer.post(base, {"name": "Application"}, content_type="application/json")
    detail = base + created.json()["public_id"] + "/"
    bad = {"fields": [{"id": "pitch", "type": "unknown", "label": "Pitch"}]}
    assert (
        organizer.put(detail, {"schema": bad}, content_type="application/json").status_code == 400
    )
    assert organizer.get(detail + "versions/").json() == []
    event.status = "archived"
    event.save(update_fields=["status"])
    assert organizer.post(detail + "publish/").status_code == 400
