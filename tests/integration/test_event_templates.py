import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event, Track
from integrations.models import EventTemplate
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def fixture():
    user = User.objects.create_user(username="tpl-organizer", password="unused")
    workspace = Workspace.objects.create(name="Templates", slug="templates")
    Membership.objects.create(user=user, workspace=workspace, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="Source", slug="source")
    Track.objects.create(event=event, name="Hardware")
    Stage.objects.create(event=event, name="Finals", is_initial=True)
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return workspace, event, client


def templates_url(workspace):
    return f"/api/v1/workspaces/{workspace.public_id}/event-templates/"


def test_save_instantiate_and_delete_a_template():
    workspace, event, client = fixture()
    assert Client().get(templates_url(workspace)).status_code in (401, 403)

    created = client.post(
        templates_url(workspace),
        {"event": str(event.public_id), "name": "Regional starter kit"},
        content_type="application/json",
    )
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "Regional starter kit"
    assert body["source_event_name"] == "Source"
    assert "tracks" in body["sections"]
    template = EventTemplate.objects.get(public_id=body["public_id"])
    assert template.archive["tracks"][0]["name"] == "Hardware"

    listed = client.get(templates_url(workspace)).json()
    assert len(listed) == 1

    instantiated = client.post(
        templates_url(workspace) + f"{template.public_id}/instantiate/",
        {"name": "Spring Regional", "slug": "spring-regional"},
        content_type="application/json",
    )
    assert instantiated.status_code == 201
    new_event = Event.objects.get(slug="spring-regional")
    assert new_event.tracks.get().name == "Hardware"
    assert new_event.stages.get().name == "Finals"
    assert new_event.workspace_id == workspace.id

    deleted = client.delete(templates_url(workspace) + f"{template.public_id}/")
    assert deleted.status_code == 204
    assert not EventTemplate.objects.filter(pk=template.pk).exists()


def test_direct_clone_with_a_section_subset_never_carries_a_stage_graph():
    workspace, event, client = fixture()
    clone_url = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/clone/"
    response = client.post(
        clone_url,
        {"name": "Config only", "slug": "config-only", "sections": ["tracks"]},
        content_type="application/json",
    )
    assert response.status_code == 201
    cloned = Event.objects.get(slug="config-only")
    assert cloned.tracks.get().name == "Hardware"
    assert cloned.stages.count() == 0


def test_unknown_section_is_a_bad_request():
    workspace, event, client = fixture()
    clone_url = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/clone/"
    response = client.post(
        clone_url,
        {"name": "X", "slug": "x", "sections": ["not-a-section"]},
        content_type="application/json",
    )
    assert response.status_code == 400
