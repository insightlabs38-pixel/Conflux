import xml.etree.ElementTree as ET

import pytest
from awards.models import Award, AwardWinner
from django.test import Client
from events.models import Event, EventStatus
from presentation.models import Page, PageBlock
from projects.models import Project
from test_public_site import make_public_event_with_finalized_project

pytestmark = pytest.mark.django_db


@pytest.fixture
def case():
    event, project, _ = make_public_event_with_finalized_project()
    award = Award.objects.create(
        event=event,
        name="Best in Show",
        description="Built for impact.",
        published_at="2026-01-03T00:00:00Z",
    )
    AwardWinner.objects.create(
        award=award,
        project=project,
        selected_by=project.created_by,
        source="manual",
        evidence={"private": "secret-selection-evidence"},
        override_reason="private-override",
    )
    base = f"/e/{event.public_id}/results/"
    return event, project, award, base


def paths(case):
    base = case[3]
    return [
        base,
        base + f"awards/{case[2].public_id}/",
        base + f"awards/{case[2].public_id}/card.svg",
        base + f"projects/{case[1].public_id}/",
        base + f"projects/{case[1].public_id}/card.svg",
    ]


def test_stories_render_published_results_and_share_links(case):
    urls = paths(case)
    for path in (urls[0], urls[1], urls[3]):
        response = Client().get(path)
        assert response.status_code == 200
        body = response.content.decode()
        assert "Best in Show" in body and "Autograder" in body
        assert "secret-selection-evidence" not in body and "private-override" not in body
        assert "Private notes" not in body
        assert "no-store" in response["Cache-Control"]
    award_body = Client().get(urls[1]).content.decode()
    assert urls[3] in award_body and "Built for impact." in award_body
    assert 'property="og:image"' in award_body and urls[2] in award_body
    assert 'rel="canonical"' in award_body
    assert urls[2] + "?download=1" in award_body
    project_body = Client().get(urls[3]).content.decode()
    assert "Grades things." in project_body
    assert f"/e/{case[0].public_id}/projects/{case[1].public_id}/" in project_body


def test_cards_are_self_contained_downloadable_svg(case):
    for path in (paths(case)[2], paths(case)[4]):
        response = Client().get(path)
        assert response.status_code == 200
        assert response["Content-Type"] == "image/svg+xml"
        root = ET.fromstring(response.content)
        assert root.attrib["viewBox"] == "0 0 1200 630"
        assert "default-src 'none'" in response["Content-Security-Policy"]
        assert "no-store" in response["Cache-Control"]
        downloaded = Client().get(path, {"download": "1"})
        assert downloaded["Content-Disposition"].startswith('attachment; filename="conflux-result-')
        assert "script" not in {element.tag.rsplit("}", 1)[-1] for element in root.iter()}
        assert "image" not in {element.tag.rsplit("}", 1)[-1] for element in root.iter()}


@pytest.mark.parametrize("status,public", [("draft", True), ("open", False)])
def test_all_result_surfaces_require_public_event(case, status, public):
    event = case[0]
    event.status, event.is_public = status, public
    event.save()
    for path in paths(case):
        assert Client().get(path).status_code == 404


@pytest.mark.parametrize("status", [EventStatus.CLOSED, EventStatus.ARCHIVED])
def test_published_highlights_survive_event_closing(case, status):
    case[0].status = status
    case[0].save()
    for path in paths(case):
        assert Client().get(path).status_code == 200


def test_unpublished_awards_never_generate_stories_or_cards(case):
    case[2].published_at = None
    case[2].save()
    assert "Best in Show" not in Client().get(paths(case)[0]).content.decode()
    for path in paths(case)[1:]:
        assert Client().get(path).status_code == 404


def test_reopened_project_cannot_be_shared_as_public_winner(case):
    case[1].submissions.update(status="draft")
    for path in (paths(case)[3], paths(case)[4]):
        assert Client().get(path).status_code == 404
    for path in paths(case)[:3]:
        response = Client().get(path)
        assert response.status_code == 200
        assert "Autograder" not in response.content.decode()


def test_cross_event_sources_cannot_be_shared(case):
    event = Event.objects.create(
        workspace=case[0].workspace, name="Other", slug="other", status="open", is_public=True
    )
    for path in paths(case)[1:]:
        foreign = path.replace(str(case[0].public_id), str(event.public_id))
        assert Client().get(foreign).status_code == 404
    hidden = Project.objects.create(
        event=event, created_by=case[1].created_by, name="Foreign hidden project"
    )
    AwardWinner.objects.create(
        award=case[2], project=hidden, selected_by=case[1].created_by, source="manual"
    )
    assert "Foreign hidden project" not in Client().get(paths(case)[1]).content.decode()


def test_html_and_svg_escape_untrusted_text(case):
    case[0].name = 'Event & "quotes" <script>alert(1)</script>'
    case[0].save()
    case[1].name = '<script>alert(2)</script> & "Project"'
    case[1].description = "<img src=x onerror=alert(3)> [link](javascript:alert(4))"
    case[1].save()
    case[2].name = "<script>alert(5)</script> & Award"
    case[2].description = "<img src=x onerror=alert(6)>"
    case[2].save()
    for path in (paths(case)[1], paths(case)[3]):
        body = Client().get(path).content.decode()
        assert "<script>alert(" not in body and "<img src=x" not in body
        assert 'href="javascript:' not in body
    for path in (paths(case)[2], paths(case)[4]):
        root = ET.fromstring(Client().get(path).content)
        assert all(
            element.tag.rsplit("}", 1)[-1] not in {"script", "foreignObject", "a", "image"}
            for element in root.iter()
        )
        assert not any(
            any(key.startswith("on") for key in element.attrib) for element in root.iter()
        )


def test_long_names_and_xml_controls_produce_valid_bounded_cards(case):
    case[1].name = "界" * 190 + "\x01"
    case[1].save()
    response = Client().get(paths(case)[4])
    root = ET.fromstring(response.content)
    texts = list(root.iter("{http://www.w3.org/2000/svg}text"))
    assert len(texts) <= 8
    assert "…" in response.content.decode()
    assert b"\x01" not in response.content


def test_results_are_paginated_and_invalid_page_rejected(case):
    Award.objects.bulk_create(
        [
            Award(event=case[0], name=f"Award {i:02d}", published_at="2026-01-03T00:00:00Z")
            for i in range(51)
        ]
    )
    first = Client().get(case[3]).content.decode()
    assert "Award 00" in first and "Award 50" not in first
    second = Client().get(case[3], {"page": 2}).content.decode()
    assert "Award 50" in second and "Award 00" not in second
    for number in ("0", "3", "bogus"):
        assert Client().get(case[3], {"page": number}).status_code == 404


def test_existing_results_block_links_to_award_highlight(case):
    page = Page.objects.create(event=case[0])
    PageBlock.objects.create(page=page, kind="results", position=0, config={})
    body = Client().get(f"/e/{case[0].public_id}/").content.decode()
    assert paths(case)[1] in body


def test_story_surfaces_are_read_only_and_support_head(case):
    for path in paths(case):
        assert Client().post(path).status_code == 405
        assert Client().head(path).status_code == 200
