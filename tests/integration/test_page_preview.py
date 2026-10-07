"""The organizer's preview of the public page with an unsaved appearance (PREVIEW_CONTEXT surface
`page`, PD-F004-B03-T07)."""

import json

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from django.test import Client
from events.models import Event, EventStatus
from presentation.models import Page, PageBlock
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

ART = "https://art.example.org/hero.jpg"


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="W", slug="w")
    people = {}
    for name, role in (("org", Role.ORGANIZER), ("par", Role.PARTICIPANT), ("judge", Role.JUDGE)):
        user = User.objects.create_user(username=name, password="unused")
        Membership.objects.create(user=user, workspace=workspace, role=role)
        people[name] = user
    # a draft event that is not public: the organizer can still see how its page will look
    event = Event.objects.create(
        workspace=workspace, name="Regionals", slug="r", status=EventStatus.DRAFT
    )
    return {"workspace": workspace, "event": event, "people": people}


def ask(world, who="org", event=None, **body):
    client = Client()
    client.cookies["session"] = Session.issue(world["people"][who]).token
    body.setdefault("ref", {"event": str((event or world["event"]).public_id)})
    url = f"/api/v1/workspaces/{world['workspace'].public_id}/preview-as/page/"
    return client.post(url, data=json.dumps(body), content_type="application/json")


def html(response):
    assert response.status_code == 200, response.content
    return response.json()["data"]["html"]


def test_an_unsaved_appearance_is_drawn_by_the_real_template_and_nothing_is_stored(world):
    PageBlock.objects.create(
        page=Page.objects.create(event=world["event"]),
        kind="hero",
        config={"title": "Welcome to Regionals"},
    )
    before = (Page.objects.count(), PageBlock.objects.count(), AuditEvent.objects.count())
    saved = Page.objects.get().theme_config
    page = html(ask(world))
    assert 'data-hero-size="compact"' in page and "Welcome to Regionals" in page
    draft = {
        "theme": "dark",
        "theme_config": {"hero_size": "immersive", "banner_url": ART, "banner_focus_x": 20},
    }
    page = html(ask(world, input=draft))
    assert 'data-hero-size="immersive"' in page
    assert f'src="{ART}"' in page and "--hero-focus-x:20%" in page
    assert 'data-theme="dark"' in page and "Welcome to Regionals" in page  # the saved blocks
    assert (Page.objects.count(), PageBlock.objects.count(), AuditEvent.objects.count()) == before
    assert Page.objects.get().theme_config == saved  # the stored appearance did not move
    assert Page.objects.get().theme == "default"


def test_an_event_with_no_page_yet_previews_the_default_and_still_creates_nothing(world):
    page = html(ask(world, input={"theme_config": {"hero_size": "none"}}))
    assert 'data-hero-size="none"' in page and "Regionals" in page
    assert Page.objects.count() == 0


def test_a_draft_the_server_would_refuse_to_save_is_refused_with_the_same_reason(world):
    refused = ask(world, input={"theme_config": {"hero_size": "immersive"}})
    assert refused.status_code == 400
    assert "built around artwork" in str(refused.json()["input.theme_config"])
    low = ask(world, input={"theme_config": {"accent": "#ffffff"}})
    assert low.status_code == 400 and "4.5:1" in str(low.json())
    unknown = ask(world, input={"theme_config": {"css": "body{display:none}"}})
    assert unknown.status_code == 400
    unsupported = ask(world, input={"theme_config": {"hero_size": "huge"}})
    assert unsupported.status_code == 400
    focus = ask(world, input={"theme_config": {"banner_url": ART, "banner_focus_x": 101}})
    assert focus.status_code == 400


def test_only_organizers_preview_and_only_events_of_this_workspace(world):
    assert ask(world).status_code == 200
    for who in ("par", "judge"):
        assert ask(world, who).status_code == 403
    other = Event.objects.create(
        workspace=Workspace.objects.create(name="X", slug="x"), name="O", slug="o"
    )
    assert ask(world, event=other).status_code == 404
    assert ask(world, ref={"event": "00000000-0000-4000-8000-000000000000"}).status_code == 404
    assert ask(world, ref={}).status_code == 400


def test_the_preview_draws_no_unsafe_link_and_runs_no_script(world):
    page = Page.objects.create(event=world["event"])
    PageBlock.objects.create(
        page=page,
        kind="hero",
        config={"title": "Hi", "cta_label": "Go", "cta_href": "javascript:alert(1)"},
    )
    out = html(ask(world))
    assert "javascript:" not in out and "<script" not in out and "<noscript" not in out
