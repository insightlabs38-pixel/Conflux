from datetime import UTC, datetime

import pytest
from accounts.models import Session, User
from django.core.management import call_command
from django.test import Client
from presentation.conformance import audit_html, build_conformance_report
from presentation.models import Page, PageBlock
from test_public_site import make_public_event_with_finalized_project
from workspaces.models import Membership, Role

pytestmark = pytest.mark.django_db
NOW = datetime(2026, 9, 28, tzinfo=UTC)

GOOD = """<!doctype html><html lang="en"><head><title>T</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0"></head><body>
<a href="#main-content">Skip</a><main id="main-content"><h1>A</h1><h2>B</h2>
<img src="x.png" alt="x"><a href="/x">Gallery</a>
<label for="q">Search</label><input id="q" name="q"><button>Go</button></main></body></html>"""


def failed(html):
    return {c["check"]: c["evidence"] for c in audit_html(html) if c["outcome"] == "fail"}


def test_clean_document_passes_every_check():
    assert failed(GOOD) == {}


@pytest.mark.parametrize(
    ("html", "check"),
    [
        (GOOD.replace('lang="en"', ""), "language"),
        (GOOD.replace("<title>T</title>", "<title> </title>"), "title"),
        (GOOD.replace("<h2>B</h2>", "<h1>B</h1>"), "single-h1"),
        (GOOD.replace("<h2>B</h2>", "<h3>B</h3>"), "heading-order"),
        (GOOD.replace('<a href="#main-content">Skip</a>', ""), "landmarks"),
        (GOOD.replace('href="#main-content"', 'href="#gone"'), "landmarks"),
        (GOOD.replace('alt="x"', ""), "image-alt"),
        (GOOD.replace(">Gallery<", ">click here<"), "link-name"),
        (GOOD.replace(">Gallery<", "><"), "link-name"),
        (GOOD.replace('<label for="q">Search</label>', ""), "control-label"),
        (GOOD.replace("<button>Go</button>", "<button></button>"), "button-name"),
        (GOOD.replace("</main>", '<iframe src="/e"></iframe></main>'), "frame-title"),
        (GOOD.replace("initial-scale=1.0", "user-scalable=no"), "zoom"),
        (GOOD.replace("<h2>B</h2>", '<h2 tabindex="3">B</h2>'), "tabindex"),
        (GOOD.replace("<h2>B</h2>", '<h2 id="q">B</h2>'), "unique-id"),
        (GOOD.replace("</main>", "<table><tr><td>1</td></tr></table></main>"), "table-headers"),
    ],
)
def test_each_defect_is_detected_with_evidence(html, check):
    found = failed(html)
    assert check in found


def test_named_by_image_or_aria_and_wrapping_label_pass():
    html = GOOD.replace(
        "<button>Go</button>",
        '<a href="/a"><img src="l.png" alt="Home"></a><a href="/b" aria-label="Docs"></a>'
        '<label>Email <input name="e"></label><button aria-label="Close"></button>',
    )
    assert failed(html) == {}


def test_report_covers_reachable_pages_and_never_claims_conformance():
    event, project, _ = make_public_event_with_finalized_project()
    page = Page.objects.create(event=event)
    PageBlock.objects.create(page=page, kind="hero", position=0, config={"title": "Hi"})
    report = build_conformance_report(event, now=NOW)
    assert report["conformance_claimed"] is False and report["manual_review"]
    by_path = {p["path"]: p for p in report["pages"]}
    landing = by_path[f"/e/{event.public_id}/"]
    assert landing["status"] == 200 and len(landing["sha256"]) == 64
    assert {c["check"] for c in landing["checks"]} >= {"language", "landmarks", "link-name"}
    assert f"/e/{event.public_id}/projects/{project.public_id}/" in by_path
    assert by_path[f"/e/{event.public_id}/finalists/"]["status"] == 404
    assert report["summary"]["pages_audited"] + report["summary"]["pages_unavailable"] == len(
        report["pages"]
    )
    assert report == build_conformance_report(event, now=NOW)


def test_dark_theme_contrast_is_included():
    event, _, _ = make_public_event_with_finalized_project()
    Page.objects.create(event=event, theme="dark")
    assert build_conformance_report(event, now=NOW)["theme"]["name"] == "dark"


def test_endpoint_is_organizer_only_and_command_prints_json(capsys):
    event, project, _ = make_public_event_with_finalized_project()
    organizer = User.objects.create_user(username="org", password="unused")
    Membership.objects.create(workspace=event.workspace, user=organizer, role=Role.ORGANIZER)
    url = (
        f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}"
        "/accessibility-conformance/"
    )
    assert Client().get(url).status_code in (401, 403)
    participant = Client()
    participant.cookies["session"] = Session.issue(project.created_by).token
    assert participant.get(url).status_code == 403
    client = Client()
    client.cookies["session"] = Session.issue(organizer).token
    response = client.get(url)
    assert response.status_code == 200 and response.json()["event"] == str(event.public_id)
    call_command("accessibility_conformance", str(event.public_id))
    assert '"conformance_claimed": false' in capsys.readouterr().out
