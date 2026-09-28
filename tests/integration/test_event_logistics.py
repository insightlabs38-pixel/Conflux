import re
from datetime import timedelta

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from django.test import Client
from django.utils import timezone
from events.models import Event, Track
from onsite import agenda
from onsite.models import AgendaSession, Location, ProjectLocation
from projects.models import (
    Project,
    ProjectMembership,
    Submission,
    SubmissionStatus,
    SubmissionVersion,
)
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def post(client, url, data):
    return client.post(url, data, content_type="application/json")


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="L", slug="l")
    now = timezone.now()
    event = Event.objects.create(
        workspace=workspace,
        name="Logistics Fest",
        slug="lf",
        status="open",
        is_public=True,
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(hours=8),
    )
    organizer = User.objects.create_user(username="org")
    member = User.objects.create_user(username="mem")
    Membership.objects.create(workspace=workspace, user=organizer, role=Role.ORGANIZER)
    Membership.objects.create(workspace=workspace, user=member, role=Role.PARTICIPANT)
    return dict(workspace=workspace, event=event, organizer=organizer, member=member, now=now)


def api(w, suffix=""):
    return f"/api/v1/workspaces/{w['workspace'].public_id}/events/{w['event'].public_id}/{suffix}"


def payload(w, **extra):
    now = w["now"]
    return {
        "title": "Opening keynote",
        "starts_at": (now + timedelta(hours=1)).isoformat(),
        "ends_at": (now + timedelta(hours=2)).isoformat(),
        **extra,
    }


# API


def test_organizers_manage_sessions_and_everything_is_audited(world):
    w = world
    org = client_for(w["organizer"])
    room = Location.objects.create(event=w["event"], kind="room", name="Hall A")
    track = Track.objects.create(event=w["event"], name="AI")
    created = post(
        org,
        api(w, "agenda/"),
        payload(w, location=str(room.public_id), track=str(track.public_id), speakers="Ada, Bob"),
    )
    assert created.status_code == 201, created.content
    sid = created.json()["public_id"]
    patched = org.patch(
        api(w, f"agenda/{sid}/"), {"title": "Keynote"}, content_type="application/json"
    )
    assert patched.json()["title"] == "Keynote" and patched.json()["location"] == str(
        room.public_id
    )
    assert len(org.get(api(w, "agenda/")).json()) == 1
    assert org.delete(api(w, f"agenda/{sid}/")).status_code == 204
    actions = list(
        AuditEvent.objects.filter(action__startswith="agenda.").values_list("action", flat=True)
    )
    assert sorted(actions) == [
        "agenda.session_created",
        "agenda.session_deleted",
        "agenda.session_updated",
    ]


def test_only_organizers_can_write_the_agenda(world):
    w = world
    member = client_for(w["member"])
    assert post(member, api(w, "agenda/"), payload(w)).status_code == 403
    assert member.get(api(w, "agenda/")).status_code == 403
    assert post(Client(), api(w, "agenda/"), payload(w)).status_code in (401, 403)


@pytest.mark.parametrize(
    "patch",
    [
        {"ends_at": "past"},
        {"stream_url": "http://insecure.example/x"},
        {"stream_url": "javascript:alert(1)"},
        {"stream_url": "https://user:pw@example.test/x"},
        {"title": ""},
        {"title": "x" * 201},
        {"bogus": 1},
        {"location": "00000000-0000-0000-0000-000000000000"},
    ],
)
def test_invalid_sessions_are_rejected(world, patch):
    w = world
    body = payload(w)
    if patch.get("ends_at") == "past":
        patch = {"ends_at": (w["now"]).isoformat()}
    assert post(client_for(w["organizer"]), api(w, "agenda/"), {**body, **patch}).status_code in (
        400,
        404,
    )
    assert not AgendaSession.objects.exists()


def test_locations_and_tracks_from_other_events_are_refused(world):
    w = world
    other = Event.objects.create(workspace=w["workspace"], name="Other", slug="o")
    foreign = Location.objects.create(event=other, kind="room", name="Elsewhere")
    response = post(
        client_for(w["organizer"]), api(w, "agenda/"), payload(w, location=str(foreign.public_id))
    )
    assert response.status_code == 404


# Embed policy


@pytest.mark.parametrize(
    "url,expected",
    [
        (
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
        ),
        ("https://youtu.be/dQw4w9WgXcQ", "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"),
        (
            "https://youtube.com/embed/dQw4w9WgXcQ",
            "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
        ),
        ("https://vimeo.com/123456789", "https://player.vimeo.com/video/123456789"),
        ("https://www.youtube.com/watch?v=short", None),
        ('https://www.youtube.com/watch?v="><script>', None),
        ("https://youtube.com.evil.test/watch?v=dQw4w9WgXcQ", None),
        ("https://evil.test/embed/dQw4w9WgXcQ", None),
        ("https://vimeo.com/not-a-number", None),
        ("", None),
    ],
)
def test_only_known_video_hosts_are_framed(url, expected):
    assert agenda.embed_url(url) == expected


def test_operator_trusted_hosts_are_framed_verbatim(settings):
    settings.EMBED_HOSTS = ["stream.campus.test"]
    assert (
        agenda.embed_url("https://stream.campus.test/live/1") == "https://stream.campus.test/live/1"
    )
    assert agenda.embed_url("https://other.test/live/1") is None


# Public surfaces


def add_session(w, **kw):
    now = w["now"]
    defaults = dict(
        event=w["event"],
        title="Talk",
        starts_at=now + timedelta(hours=1),
        ends_at=now + timedelta(hours=2),
    )
    defaults.update(kw)
    return AgendaSession.objects.create(**defaults)


def test_agenda_page_frames_known_streams_links_others_and_hides_private_sessions(world):
    w = world
    add_session(w, title="Framed", stream_url="https://youtu.be/dQw4w9WgXcQ")
    add_session(w, title="Linked", stream_url="https://example.test/live")
    add_session(w, title="Secret", is_public=False)
    html = Client().get(f"/e/{w['event'].public_id}/agenda/").content.decode()
    assert (
        html.count("<iframe") == 1
        and 'sandbox="allow-scripts allow-same-origin allow-presentation"' in html
    )
    assert "youtube-nocookie.com/embed/dQw4w9WgXcQ" in html
    assert 'href="https://example.test/live"' in html and "Secret" not in html
    assert f"/e/{w['event'].public_id}/agenda.ics" in html


def test_agenda_page_escapes_hostile_text(world):
    w = world
    add_session(w, title="<script>alert(1)</script>", description="<img src=x onerror=1>")
    html = Client().get(f"/e/{w['event'].public_id}/agenda/").content.decode()
    assert "<script>alert(1)" not in html and "&lt;script&gt;" in html and "<img src=x" not in html


def test_unpublished_events_expose_nothing(world):
    w = world
    add_session(w)
    Event.objects.filter(pk=w["event"].pk).update(status="draft")
    for path in ("agenda/", "agenda.ics", "map/", "badge.svg"):
        assert Client().get(f"/e/{w['event'].public_id}/{path}").status_code == 404
    for path in ("agenda/", "state/"):
        assert Client().get(f"/api/v1/events/{w['event'].public_id}/{path}").status_code == 404


def unfold(text):
    return text.replace("\r\n ", "")


def test_ics_is_valid_folded_escaped_and_injection_safe(world):
    w = world
    room = Location.objects.create(event=w["event"], kind="room", name="Hall; A, B")
    session = add_session(
        w,
        title="Semi;colon, comma\r\nBEGIN:VEVENT\r\nSUMMARY:pwn",
        description="é" * 120 + "\nsecond line",
        location=room,
        stream_url="https://example.test/live",
    )
    add_session(w, title="Private", is_public=False)
    response = Client().get(f"/e/{w['event'].public_id}/agenda.ics")
    assert response["Content-Type"].startswith("text/calendar")
    raw = response.content.decode()
    assert raw.startswith("BEGIN:VCALENDAR\r\n") and raw.endswith("END:VCALENDAR\r\n")
    assert all(len(line.encode()) <= 75 for line in raw.split("\r\n"))
    text = unfold(raw)
    lines = text.split("\r\n")
    assert lines.count("BEGIN:VEVENT") == 1 and lines.count("END:VEVENT") == 1
    assert "Private" not in text
    assert r"SUMMARY:Semi\;colon\, comma\nBEGIN:VEVENT\nSUMMARY:pwn" in text
    assert r"LOCATION:Hall\; A\, B" in text and "URL:https://example.test/live" in text
    assert re.search(r"DTSTART:\d{8}T\d{6}Z", text)
    assert f"UID:{session.public_id}@testserver" in text
    assert Client().get(f"/e/{w['event'].public_id}/agenda.ics").content == response.content


def test_state_endpoint_reports_phase_live_and_next_sessions(world):
    w = world
    now = w["now"]
    add_session(
        w, title="Now", starts_at=now - timedelta(minutes=10), ends_at=now + timedelta(minutes=20)
    )
    add_session(
        w, title="Later", starts_at=now + timedelta(hours=2), ends_at=now + timedelta(hours=3)
    )
    add_session(
        w,
        title="Hidden",
        starts_at=now + timedelta(minutes=30),
        ends_at=now + timedelta(hours=1),
        is_public=False,
    )
    response = Client().get(f"/api/v1/events/{w['event'].public_id}/state/")
    body = response.json()
    assert body["phase"] == "live" and body["live_sessions"] == ["Now"]
    assert body["next_session"]["title"] == "Later" and body["projects"] == 0
    assert response["Access-Control-Allow-Origin"] == "*"
    Event.objects.filter(pk=w["event"].pk).update(status="closed")
    assert Client().get(f"/api/v1/events/{w['event'].public_id}/state/").json()["phase"] == "ended"
    Event.objects.filter(pk=w["event"].pk).update(
        status="open", starts_at=now + timedelta(days=1), ends_at=now + timedelta(days=2)
    )
    assert (
        Client().get(f"/api/v1/events/{w['event'].public_id}/state/").json()["phase"] == "upcoming"
    )


def test_badge_is_an_escaped_svg_reflecting_the_phase(world):
    w = world
    Event.objects.filter(pk=w["event"].pk).update(name='<b>&"Fest"')
    response = Client().get(f"/e/{w['event'].public_id}/badge.svg")
    body = response.content.decode()
    assert response["Content-Type"] == "image/svg+xml" and "LIVE" in body
    assert "<b>" not in body and "&lt;b&gt;" in body and 'role="img"' in body


def test_public_agenda_json_matches_the_visible_sessions(world):
    w = world
    add_session(w, title="Public", stream_url="https://vimeo.com/123456789")
    add_session(w, title="Private", is_public=False)
    items = Client().get(f"/api/v1/events/{w['event'].public_id}/agenda/").json()
    assert [i["title"] for i in items] == ["Public"]
    assert items[0]["embed_url"] == "https://player.vimeo.com/video/123456789"


def test_expo_map_lists_tables_with_only_publicly_visible_projects(world):
    w = world
    event = w["event"]
    stage = Stage.objects.create(event=event, name="Final")
    room = Location.objects.create(event=event, kind="room", name="Hall")
    table = Location.objects.create(event=event, kind="table", name="T1", parent=room)
    Location.objects.create(event=event, kind="booth", name="B9")

    def project(name, finalized):
        item = Project.objects.create(event=event, name=name, created_by=w["member"])
        ProjectMembership.objects.create(project=item, user=w["member"], role="owner")
        submission = Submission.objects.create(project=item, stage=stage, updated_by=w["member"])
        if finalized:
            version = SubmissionVersion.objects.create(
                submission=submission,
                number=1,
                snapshot={"draft": {}, "artifacts": [], "forms": []},
                digest="c" * 64,
                finalized_by=w["member"],
            )
            submission.status = SubmissionStatus.FINALIZED
            submission.current_version = version
            submission.save()
        ProjectLocation.objects.create(project=item, location=table)
        return item

    project("Shown Bot", True)
    project("Draft Bot", False)
    html = Client().get(f"/e/{event.public_id}/map/").content.decode()
    assert "Shown Bot" in html and "Draft Bot" not in html
    assert "Table T1" in html and "Booth B9" in html and "Hall" in html
    assert "Room Hall" not in html


def test_agenda_page_shows_times_in_utc_regardless_of_server_timezone(world, settings):
    w = world
    settings.TIME_ZONE = "Pacific/Auckland"
    start = w["now"].replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
    add_session(w, title="Nine", starts_at=start, ends_at=start + timedelta(hours=1))
    html = Client().get(f"/e/{w['event'].public_id}/agenda/").content.decode()
    assert "09:00" in html and "10:00" in html
