import pytest
from django.test import Client
from events.models import BasePrize, Event, EventStatus, Track
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def _open_public_event():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(
        workspace=workspace,
        name="Regionals",
        slug="regionals",
        status=EventStatus.OPEN,
        is_public=True,
        starts_at="2026-01-01T00:00:00Z",
        ends_at="2026-01-02T00:00:00Z",
    )
    track = Track.objects.create(event=event, name="AI", position=0)
    BasePrize.objects.create(
        event=event, track=track, name="Best AI", kind=BasePrize.Kind.SWAG, position=0
    )
    return event


def test_public_event_view_exposes_tracks_and_prizes_for_the_landing_page():
    event = _open_public_event()
    response = Client().get(f"/api/v1/events/{event.public_id}/")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Regionals"
    assert [track["name"] for track in body["tracks"]] == ["AI"]
    assert [prize["name"] for prize in body["base_prizes"]] == ["Best AI"]
    assert body["base_prizes"][0]["track"] == str(event.tracks.get().public_id)


def test_public_event_view_hides_non_public_or_unopened_events():
    workspace = Workspace.objects.create(name="W", slug="w")
    draft = Event.objects.create(workspace=workspace, name="Draft", slug="draft", is_public=True)
    private = Event.objects.create(
        workspace=workspace,
        name="Private",
        slug="private",
        status=EventStatus.OPEN,
        is_public=False,
        starts_at="2026-01-01T00:00:00Z",
        ends_at="2026-01-02T00:00:00Z",
    )
    client = Client()
    assert client.get(f"/api/v1/events/{draft.public_id}/").status_code == 404
    assert client.get(f"/api/v1/events/{private.public_id}/").status_code == 404


def test_public_event_view_stays_readable_after_the_event_closes_and_is_archived():
    """S19: the public event page is a stable post-event archive, not
    something that 404s the moment an organizer closes or archives it.
    """
    event = _open_public_event()
    client = Client()

    event.status = EventStatus.CLOSED
    event.save(update_fields=["status"])
    closed = client.get(f"/api/v1/events/{event.public_id}/")
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"

    event.status = EventStatus.ARCHIVED
    event.save(update_fields=["status"])
    archived = client.get(f"/api/v1/events/{event.public_id}/")
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
