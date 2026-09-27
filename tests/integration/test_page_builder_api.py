import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
from presentation.models import Page, PageBlock
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def cookie_client(token):
    client = Client()
    client.cookies["session"] = token
    return client


def make_event_with_organizer():
    organizer = User.objects.create_user(username="organizer", password="unused")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    return workspace, event, organizer


def page_url(workspace, event, suffix=""):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/page/{suffix}"


def test_organizer_can_read_and_update_theme_lazily_creating_the_page():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(Session.issue(organizer).token)

    response = client.get(page_url(workspace, event))
    assert response.status_code == 200
    assert response.json()["theme"] == "default"
    assert Page.objects.filter(event=event).count() == 1

    response = client.patch(
        page_url(workspace, event), data={"theme": "dark"}, content_type="application/json"
    )
    assert response.status_code == 200
    assert response.json()["theme"] == "dark"


def test_anonymous_and_participant_cannot_edit_the_page():
    workspace, event, _ = make_event_with_organizer()
    participant = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(user=participant, workspace=workspace, role=Role.PARTICIPANT)

    assert Client().get(page_url(workspace, event)).status_code in (401, 403)
    participant_client = cookie_client(Session.issue(participant).token)
    assert participant_client.get(page_url(workspace, event)).status_code == 403


def test_block_create_validates_config_and_appends_position():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(Session.issue(organizer).token)

    bad = client.post(
        page_url(workspace, event, "blocks/"),
        data={"kind": "hero", "config": {}},
        content_type="application/json",
    )
    assert bad.status_code == 400

    first = client.post(
        page_url(workspace, event, "blocks/"),
        data={"kind": "hero", "config": {"title": "Welcome"}},
        content_type="application/json",
    )
    assert first.status_code == 201
    assert first.json()["position"] == 0

    second = client.post(
        page_url(workspace, event, "blocks/"),
        data={"kind": "tracks", "config": {}},
        content_type="application/json",
    )
    assert second.status_code == 201
    assert second.json()["position"] == 1


def test_rich_text_block_is_sanitized_on_save():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(Session.issue(organizer).token)
    response = client.post(
        page_url(workspace, event, "blocks/"),
        data={
            "kind": "rich_text",
            "config": {"html": '<p onclick="evil()">Hi <script>alert(1)</script></p>'},
        },
        content_type="application/json",
    )
    assert response.status_code == 201
    assert response.json()["config"]["html"] == "<p>Hi </p>"


def test_reorder_requires_the_exact_set_of_existing_blocks():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(Session.issue(organizer).token)
    page = Page.objects.create(event=event)
    a = PageBlock.objects.create(page=page, kind="tracks", position=0)
    b = PageBlock.objects.create(page=page, kind="prizes", position=1)

    ok = client.post(
        page_url(workspace, event, "blocks/reorder/"),
        data={"block_ids": [str(b.public_id), str(a.public_id)]},
        content_type="application/json",
    )
    assert ok.status_code == 200
    b.refresh_from_db()
    a.refresh_from_db()
    assert (b.position, a.position) == (0, 1)

    bad = client.post(
        page_url(workspace, event, "blocks/reorder/"),
        data={"block_ids": [str(a.public_id)]},
        content_type="application/json",
    )
    assert bad.status_code == 400


def test_block_delete_removes_it():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(Session.issue(organizer).token)
    page = Page.objects.create(event=event)
    block = PageBlock.objects.create(page=page, kind="tracks", position=0)

    response = client.delete(page_url(workspace, event, f"blocks/{block.public_id}/"))
    assert response.status_code == 204
    assert not PageBlock.objects.filter(pk=block.pk).exists()
