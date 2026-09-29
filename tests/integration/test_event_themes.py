import pytest
from accounts.models import Session
from django.core.exceptions import ValidationError
from presentation.models import Page
from presentation.themes import PRESETS, clean_theme_config, resolved_theme
from test_page_builder_api import cookie_client, make_event_with_organizer, page_url

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "config",
    [
        {"css": "body{display:none}"},
        {"accent": "red"},
        {"accent": "#ffffff"},
        {"hero": "anything"},
        {"logo_url": "javascript:alert(1)"},
        {"banner_url": 'https://example.org/a" onload=evil'},
        {"width": []},
    ],
)
def test_rejects_unconstrained_or_inaccessible_theme_settings(config):
    with pytest.raises(ValidationError):
        clean_theme_config(config)


def test_presets_are_structurally_distinct_and_have_usable_controls():
    settings = [resolved_theme(Page(theme_config=config)) for config in PRESETS.values()]
    assert len({item["hero"] for item in settings}) == 3
    assert len({item["typography"] for item in settings}) == 3
    for item in settings:
        assert item["variables"]["--color-accent"] == item["variables"]["--color-focus-ring"]


def test_theme_api_validates_combined_mode_and_settings_without_overwriting_on_failure():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(Session.issue(organizer).token)
    url = page_url(workspace, event)
    client.get(url)
    response = client.patch(
        url, {"theme_config": PRESETS["student"]}, content_type="application/json"
    )
    assert response.status_code == 200
    assert response.json()["theme_config"]["hero"] == "poster"
    response = client.patch(url, {"theme": "dark"}, content_type="application/json")
    assert response.status_code == 400
    page = Page.objects.get(event=event)
    assert page.theme == "default"
    assert page.theme_config == PRESETS["student"]
    response = client.patch(
        url,
        {"theme": "dark", "theme_config": {"accent": "#a8dbbf"}},
        content_type="application/json",
    )
    assert response.status_code == 200


@pytest.mark.parametrize("preset", list(PRESETS))
def test_public_server_and_react_consumers_receive_same_safe_theme(preset):
    from django.test import Client
    from presentation.models import PageBlock
    from test_public_site import make_public_event_with_finalized_project

    event, _, _ = make_public_event_with_finalized_project()
    page = Page.objects.create(event=event, theme_config=PRESETS[preset])
    PageBlock.objects.create(page=page, kind="hero", config={"title": event.name})
    response = Client().get(f"/e/{event.public_id}/")
    assert response.status_code == 200
    body = response.content.decode()
    assert f'data-hero="{PRESETS[preset]["hero"]}"' in body
    assert f'data-typography="{PRESETS[preset]["typography"]}"' in body
    public = Client().get(f"/api/v1/events/{event.public_id}/").json()
    assert public["presentation"]["hero"] == PRESETS[preset]["hero"]
    assert public["presentation"]["variables"]["--color-accent"] == PRESETS[preset]["accent"]
