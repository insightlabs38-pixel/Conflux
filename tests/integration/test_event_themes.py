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
        {"hero_size": "immersive"},
        {"hero_size": ""},
        {"hero_size": ["none"]},
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


def test_hero_size_defaults_to_compact_and_a_theme_without_it_needs_no_migration():
    assert resolved_theme(None)["hero_size"] == "compact"
    legacy = Page(theme_config={"hero": "poster", "accent": "#a32918"})
    assert resolved_theme(legacy)["hero_size"] == "compact"
    assert all("hero_size" not in preset for preset in PRESETS.values())
    for size in ("none", "compact", "standard"):
        assert resolved_theme(Page(theme_config={"hero_size": size}))["hero_size"] == size


def test_organizer_chooses_the_hero_size_and_the_public_page_follows():
    from django.test import Client
    from presentation.models import PageBlock
    from test_public_site import make_public_event_with_finalized_project

    event, _, _ = make_public_event_with_finalized_project()
    page = Page.objects.create(event=event, theme_config={"hero": "split"})
    PageBlock.objects.create(page=page, kind="hero", config={"title": event.name})

    def site():
        body = Client().get(f"/e/{event.public_id}/").content.decode()
        public = Client().get(f"/api/v1/events/{event.public_id}/").json()
        return body, public["presentation"]["hero_size"]

    body, size = site()  # stored before the setting existed: compact
    assert size == "compact" and 'data-hero-size="compact"' in body
    for chosen in ("none", "standard", "compact"):
        page.theme_config = {"hero": "split", "hero_size": chosen}
        page.save()
        body, size = site()
        assert size == chosen and f'data-hero-size="{chosen}"' in body
        assert body.count("<h1") == 1  # the page keeps its title whatever the size


def test_hero_size_is_validated_by_the_page_api_and_a_refusal_changes_nothing():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(Session.issue(organizer).token)
    url = page_url(workspace, event)
    client.get(url)
    ok = client.patch(url, {"theme_config": {"hero_size": "none"}}, content_type="application/json")
    assert ok.status_code == 200 and ok.json()["theme_config"]["hero_size"] == "none"
    bad = client.patch(
        url, {"theme_config": {"hero_size": "immersive"}}, content_type="application/json"
    )
    assert bad.status_code == 400
    assert "hero_size" in str(bad.json()) and "Unsupported" in str(bad.json())
    assert Page.objects.get(event=event).theme_config == {"hero_size": "none"}
