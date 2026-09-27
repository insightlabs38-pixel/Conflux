import pytest
from django.test import Client
from events.models import Event, EventStatus
from presentation.models import Page, PageBlock
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def public_event_with_tracks_block():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(
        workspace=workspace,
        name="Regionals",
        slug="regionals",
        status=EventStatus.OPEN,
        is_public=True,
        starts_at="2027-01-01T00:00:00Z",
        ends_at="2027-01-02T00:00:00Z",
    )
    page = Page.objects.create(event=event)
    PageBlock.objects.create(page=page, kind="tracks", position=0, config={})
    return event


def test_public_site_defaults_to_english():
    event = public_event_with_tracks_block()
    response = Client().get(f"/e/{event.public_id}/")
    body = response.content.decode()
    assert 'lang="en"' in body
    assert "Tracks will be announced soon." in body


def test_accept_language_header_renders_spanish_translations():
    event = public_event_with_tracks_block()
    response = Client().get(f"/e/{event.public_id}/", HTTP_ACCEPT_LANGUAGE="es")
    body = response.content.decode()
    assert 'lang="es"' in body
    assert "Las categorías se anunciarán pronto." in body
    assert "Saltar al contenido principal" in body


def test_set_language_cookie_persists_the_choice_across_requests():
    event = public_event_with_tracks_block()
    client = Client()
    switched = client.post(
        "/e/i18n/setlang/",
        {"language": "es", "next": f"/e/{event.public_id}/"},
    )
    assert switched.status_code == 302
    assert client.cookies["django_language"].value == "es"

    followed = client.get(f"/e/{event.public_id}/")
    assert "Las categorías se anunciarán pronto." in followed.content.decode()
