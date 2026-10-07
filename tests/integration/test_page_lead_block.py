"""The lead block (PD-F004-B03-T05) and the link rules for organizer-typed block links."""

import pytest
from accounts.models import Session
from django.core.exceptions import ValidationError
from django.test import Client
from presentation.blocks import clean_config, safe_href
from presentation.models import Page, PageBlock
from test_accessibility_audit import (
    add_block,
    audit,
    cookie_client,
    make_event_with_organizer,
    page_url,
)
from test_public_site import make_public_event_with_finalized_project

pytestmark = pytest.mark.django_db

LEAD = {
    "title": "Applications close Friday",
    "body": "Bring a laptop and a team of up to four.",
    "facts": [
        {"label": "Deadline", "value": "Fri 18:00 UTC"},
        {"label": "Team size", "value": "1-4"},
    ],
    "cta_label": "Apply now",
    "cta_href": "/apply/",
}


def test_a_lead_block_has_one_required_title_a_short_body_and_at_most_four_facts():
    cleaned = clean_config("lead", LEAD)
    assert cleaned["facts"][0] == {"label": "Deadline", "value": "Fri 18:00 UTC"}
    assert clean_config("lead", {"title": "Hi"})["facts"] == []
    for bad in (
        {"title": "  "},
        {"title": "Hi", "body": "x" * 601},
        {"title": "Hi", "facts": [{"label": "a", "value": "b"}] * 5},
    ):
        with pytest.raises(ValidationError):
            clean_config("lead", bad)


@pytest.mark.parametrize(
    "href,ok",
    [
        ("/apply/", True),
        ("gallery/", True),
        ("?q=ai", True),
        ("#rules", True),
        ("https://example.org/a?b=1", True),
        ("http://example.org", True),
        ("mailto:hello@example.org", True),
        ("javascript:alert(1)", False),
        (" JavaScript:alert(1)", False),
        ("data:text/html,<script>1</script>", False),
        ("//evil.example/x", False),
        ("/\\evil.example", False),
        ("https://", False),
        ("https://ex ample.org", False),
        ("vbscript:x", False),
        ("x:y", False),
        ("java\tscript:alert(1)", False),
        ("", False),
        (None, False),
    ],
)
def test_only_a_path_an_anchor_or_an_http_or_mailto_link_is_a_safe_href(href, ok):
    assert bool(safe_href(href)) is ok


@pytest.mark.parametrize(
    "kind,config",
    [
        ("hero", {"title": "T", "cta_label": "Go", "cta_href": "javascript:alert(1)"}),
        ("lead", {"title": "T", "cta_label": "Go", "cta_href": "data:text/html,x"}),
        ("cta", {"label": "Go", "href": "javascript:alert(1)"}),
        ("sponsors", {"items": [{"name": "A", "url": "javascript:alert(1)"}]}),
        ("resources", {"items": [{"label": "A", "url": "javascript:alert(1)"}]}),
    ],
)
def test_a_block_with_an_unsafe_link_is_refused_and_says_what_is_allowed(kind, config):
    with pytest.raises(ValidationError) as caught:
        clean_config(kind, config)
    assert "path on this site" in str(caught.value)


def test_the_page_api_refuses_an_unsafe_lead_link_and_stores_nothing():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(Session.issue(organizer).token)
    bad = client.post(
        page_url(workspace, event, "blocks/"),
        data={"kind": "lead", "config": {**LEAD, "cta_href": "javascript:alert(1)"}},
        content_type="application/json",
    )
    assert bad.status_code == 400 and "cta_href" in str(bad.json())
    assert not PageBlock.objects.filter(page__event=event).exists()
    add_block(client, workspace, event, "lead", LEAD)
    assert PageBlock.objects.filter(page__event=event, kind="lead").count() == 1


def test_a_lead_replaces_the_default_hero_with_one_h1_and_its_facts_and_action():
    event, _, _ = make_public_event_with_finalized_project()
    page = Page.objects.create(event=event)
    PageBlock.objects.create(page=page, kind="lead", position=0, config=clean_config("lead", LEAD))
    body = Client().get(f"/e/{event.public_id}/").content.decode()
    assert body.count("<h1") == 1
    assert "Applications close Friday" in body
    assert "<dt>Deadline</dt><dd>Fri 18:00 UTC</dd>" in body
    assert 'href="/apply/"' in body and ">Apply now<" in body
    assert "cx-hero__band" not in body  # no default hero beside it
    assert "Browse the projects" not in body


def test_a_link_stored_before_the_rule_existed_is_dropped_at_render_time():
    event, _, _ = make_public_event_with_finalized_project()
    page = Page.objects.create(event=event)
    for position, (kind, config) in enumerate(
        [
            ("hero", {"title": "Hi", "cta_label": "Go", "cta_href": "javascript:alert(1)"}),
            ("sponsors", {"items": [{"name": "A", "url": "javascript:alert(2)"}]}),
            ("resources", {"items": [{"label": "R", "url": "javascript:alert(3)"}]}),
            ("cta", {"label": "Go", "href": "javascript:alert(4)"}),
        ]
    ):
        PageBlock.objects.create(page=page, kind=kind, position=position, config=config)
    body = Client().get(f"/e/{event.public_id}/").content.decode()
    assert "javascript:" not in body


def test_the_accessibility_audit_counts_a_lead_as_the_pages_h1_and_checks_its_action_text():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(Session.issue(organizer).token)
    add_block(client, workspace, event, "lead", {**LEAD, "cta_label": "click here"})
    add_block(client, workspace, event, "hero", {"title": "Welcome"})
    messages = " ".join(w["message"] for w in audit(client, workspace, event))
    assert "More than one hero or lead block" in messages
    assert "doesn't describe its destination" in messages


def test_a_new_lead_opens_the_page_and_the_other_blocks_keep_their_order():
    workspace, event, organizer = make_event_with_organizer()
    client = cookie_client(Session.issue(organizer).token)
    add_block(client, workspace, event, "tracks", {})
    add_block(client, workspace, event, "faq", {})
    lead = add_block(client, workspace, event, "lead", LEAD)
    order = [b["kind"] for b in client.get(page_url(workspace, event, "blocks/")).json()]
    assert order == ["lead", "tracks", "faq"]
    assert lead["position"] == 0
    add_block(client, workspace, event, "cta", {"label": "Join us", "href": "/join/"})
    order = [b["kind"] for b in client.get(page_url(workspace, event, "blocks/")).json()]
    assert order == ["lead", "tracks", "faq", "cta"]  # other kinds still append
