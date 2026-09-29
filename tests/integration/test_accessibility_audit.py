import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
from presentation.accessibility import audit_theme, contrast_ratio
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


def add_block(client, workspace, event, kind, config):
    response = client.post(
        page_url(workspace, event, "blocks/"),
        data={"kind": kind, "config": config},
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    return response.json()


def audit(client, workspace, event):
    response = client.get(page_url(workspace, event, "accessibility-audit/"))
    assert response.status_code == 200
    return response.json()


def test_contrast_ratio_matches_known_reference_values():
    assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0, abs=0.01)
    assert contrast_ratio("#ffffff", "#000000") == contrast_ratio("#000000", "#ffffff")
    assert contrast_ratio("#ffffff", "#ffffff") == pytest.approx(1.0, abs=0.001)


def test_low_contrast_pair_is_flagged_but_all_three_real_themes_are_clean():
    assert contrast_ratio("#fefefe", "#ffffff") < 4.5

    for theme in ("default", "minimal", "dark"):
        assert audit_theme(theme) == []


def test_a_fresh_page_has_no_warnings():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(Session.issue(organizer).token)
    add_block(client, workspace, event, "hero", {"title": "Welcome"})

    assert audit(client, workspace, event) == []


def test_a_second_hero_block_is_flagged_as_a_duplicate_h1():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(Session.issue(organizer).token)
    add_block(client, workspace, event, "hero", {"title": "Welcome"})
    add_block(client, workspace, event, "hero", {"title": "Welcome again"})

    warnings = audit(client, workspace, event)
    assert any(w["category"] == "heading" and "one h1" in w["message"] for w in warnings)


def test_a_skipped_heading_level_in_rich_text_is_flagged():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(Session.issue(organizer).token)
    add_block(client, workspace, event, "rich_text", {"html": "<h2>Team</h2><h4>Sub-point</h4>"})

    warnings = audit(client, workspace, event)
    assert any(w["category"] == "heading" and "h2 to h4" in w["message"] for w in warnings)


def test_a_rich_text_section_starting_below_h2_is_flagged():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(Session.issue(organizer).token)
    add_block(client, workspace, event, "rich_text", {"html": "<h3>Details</h3>"})

    warnings = audit(client, workspace, event)
    assert any(w["category"] == "heading" and "should open at h2" in w["message"] for w in warnings)


def test_a_vague_cta_label_is_flagged():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(Session.issue(organizer).token)
    add_block(
        client,
        workspace,
        event,
        "hero",
        {"title": "Welcome", "cta_label": "Click here", "cta_href": "/gallery"},
    )

    warnings = audit(client, workspace, event)
    assert any(w["category"] == "accessible-name" for w in warnings)


def test_a_descriptive_cta_label_is_not_flagged():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(Session.issue(organizer).token)
    add_block(
        client,
        workspace,
        event,
        "hero",
        {"title": "Welcome", "cta_label": "View the project gallery", "cta_href": "/gallery"},
    )

    assert audit(client, workspace, event) == []


def test_a_link_with_no_destination_is_flagged_for_keyboard_access():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(Session.issue(organizer).token)
    add_block(client, workspace, event, "rich_text", {"html": "<p><a>Sponsors</a></p>"})

    warnings = audit(client, workspace, event)
    assert any(w["category"] == "keyboard" for w in warnings)


def test_participant_cannot_read_the_audit():
    workspace, event, organizer = make_event_with_organizer()
    participant = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(user=participant, workspace=workspace, role=Role.PARTICIPANT)
    client = cookie_client(Session.issue(participant).token)

    assert client.get(page_url(workspace, event, "accessibility-audit/")).status_code == 403


def test_fixed_theme_audit_tracks_shared_css_tokens():
    """The server audit must measure the palette actually served to browsers."""
    import re
    from pathlib import Path

    from presentation.accessibility import THEME_COLORS

    css = (Path(__file__).parents[2] / "src/web/styles/tokens.css").read_text()
    default = re.search(r":root \{(.*?)\n\}", css, re.S).group(1)
    dark = re.search(r':root\[data-theme="dark"\] \{(.*?)\n\}', css, re.S).group(1)
    for theme, section in (("default", default), ("minimal", default), ("dark", dark)):
        for key, token in (
            ("bg", "bg"),
            ("text", "text"),
            ("text_muted", "text-muted"),
            ("accent", "accent"),
        ):
            value = re.search(rf"--color-{token}: (#[0-9a-f]{{6}});", section).group(1)
            assert THEME_COLORS[theme][key] == value
