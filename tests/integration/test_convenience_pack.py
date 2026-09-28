import uuid
from datetime import timedelta

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from django.test import Client
from django.urls import get_resolver
from django.utils import timezone
from events.models import Event, Track
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
JSON = "application/json"


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="V", slug="v")
    now = timezone.now()
    event = Event.objects.create(
        workspace=workspace,
        name="Conv",
        slug="conv",
        status="open",
        is_public=True,
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(hours=8),
    )
    stage = Stage.objects.create(event=event, name="Final")
    users = {}
    for name, role in [
        ("org", Role.ORGANIZER),
        ("ada", Role.PARTICIPANT),
        ("bob", Role.PARTICIPANT),
    ]:
        users[name] = User.objects.create_user(username=name, email=f"{name}@example.test")
        Membership.objects.create(workspace=workspace, user=users[name], role=role)

    def project(name, owner):
        item = Project.objects.create(event=event, name=name, created_by=owner)
        ProjectMembership.objects.create(project=item, user=owner, role="owner")
        submission = Submission.objects.create(project=item, stage=stage, updated_by=owner)
        version = SubmissionVersion.objects.create(
            submission=submission,
            number=1,
            snapshot={"draft": {}, "artifacts": [], "forms": []},
            digest="d" * 64,
            finalized_by=owner,
        )
        submission.status = SubmissionStatus.FINALIZED
        submission.current_version = version
        submission.save()
        return item

    return dict(
        workspace=workspace,
        event=event,
        stage=stage,
        org=users["org"],
        ada=users["ada"],
        bob=users["bob"],
        ada_project=project("Ada Bot", users["ada"]),
        bob_project=project("Bob Bot", users["bob"]),
    )


def api(w, suffix=""):
    return f"/api/v1/workspaces/{w['workspace'].public_id}/events/{w['event'].public_id}/{suffix}"


def post(client, url, data=None):
    return client.post(url, data or {}, content_type=JSON)


def put(client, url, data):
    return client.put(url, data, content_type=JSON)


# Maintenance mode


def test_read_only_mode_blocks_participant_writes_but_not_reads_or_organizers(world):
    w = world
    org, ada = client_for(w["org"]), client_for(w["ada"])
    write = api(w, f"projects/{w['ada_project'].public_id}/visibility/")
    assert put(ada, write, {"gallery_visible": True}).status_code == 200
    enabled = put(org, api(w, "maintenance/"), {"read_only": True, "message": "Restoring backup"})
    assert enabled.json() == {"read_only": True, "message": "Restoring backup"}
    blocked = put(ada, write, {"gallery_visible": True})
    assert blocked.status_code == 503 and blocked.json()["detail"] == "Restoring backup"
    assert blocked["Retry-After"] == "300"
    assert ada.get(write).status_code == 200
    assert ada.get(api(w, "maintenance/")).json()["read_only"] is True
    assert put(org, write, {"gallery_visible": True}).status_code == 200
    assert put(ada, api(w, "maintenance/"), {"read_only": False}).status_code in (403, 503)
    assert put(org, api(w, "maintenance/"), {"read_only": False}).json()["read_only"] is False
    assert put(ada, write, {"gallery_visible": True}).status_code == 200
    assert AuditEvent.objects.filter(action__startswith="event.read_only").count() == 2


def test_authentication_failures_still_win_over_maintenance(world):
    w = world
    put(client_for(w["org"]), api(w, "maintenance/"), {"read_only": True})
    anonymous = post(Client(), api(w, "announcements/"), {"title": "x", "body": "y"})
    assert anonymous.status_code in (401, 403)
    stranger = User.objects.create_user(username="stranger")
    assert post(client_for(stranger), api(w, "announcements/"), {}).status_code in (403, 404)


def test_read_only_applies_to_only_the_flagged_event(world):
    w = world
    other = Event.objects.create(
        workspace=w["workspace"], name="Other", slug="other", status="open"
    )
    put(client_for(w["org"]), api(w, "maintenance/"), {"read_only": True})
    url = f"/api/v1/workspaces/{w['workspace'].public_id}/events/{other.public_id}/my-application/"
    assert client_for(w["ada"]).post(url, {}, content_type=JSON).status_code != 503


def test_every_event_scoped_write_route_refuses_a_participant_while_read_only(world):
    w = world
    put(client_for(w["org"]), api(w, "maintenance/"), {"read_only": True})
    ada = client_for(w["ada"])
    fixed = {
        "workspace_public_id": str(w["workspace"].public_id),
        "event_public_id": str(w["event"].public_id),
    }
    checked, leaks = 0, []

    def walk(patterns, prefix=""):
        for entry in patterns:
            if hasattr(entry, "url_patterns"):
                yield from walk(entry.url_patterns, prefix + str(entry.pattern))
            else:
                yield prefix + str(entry.pattern), entry

    import re

    for route, entry in walk(get_resolver().url_patterns):
        if "event_public_id" not in route or "maintenance" in route:
            continue
        cls = getattr(entry.callback, "view_class", None) or getattr(entry.callback, "cls", None)
        if cls is None:
            continue
        path = "/api/v1/" + re.sub(
            r"<(?:\w+:)?(\w+)>", lambda m: fixed.get(m.group(1), str(uuid.uuid4())), route
        ).removeprefix("api/v1/")
        for method in ("post", "put", "patch", "delete"):
            if hasattr(cls, method):
                response = getattr(ada, method)(path, {}, content_type=JSON)
                checked += 1
                if response.status_code not in (401, 403, 404, 405, 503):
                    leaks.append((method.upper(), route, response.status_code))
    assert checked > 50 and leaks == []


# Gallery visibility


def test_a_team_can_hide_its_project_from_every_public_surface(world):
    w = world
    event_id = w["event"].public_id
    ada = client_for(w["ada"])
    url = api(w, f"projects/{w['ada_project'].public_id}/visibility/")
    assert Client().get(f"/e/{event_id}/gallery/").content.decode().count("Ada Bot") >= 1
    assert put(ada, url, {"gallery_visible": False}).json() == {"gallery_visible": False}
    page = Client().get(f"/e/{event_id}/gallery/").content.decode()
    assert "Ada Bot" not in page and "Bob Bot" in page
    assert Client().get(f"/e/{event_id}/projects/{w['ada_project'].public_id}/").status_code == 404
    names = [p["name"] for p in Client().get(f"/api/v1/events/{event_id}/gallery/").json()]
    assert "Ada Bot" not in names
    found = Client().get(f"/api/v1/events/{event_id}/search/", {"q": "Ada"}).json()
    assert found["count"] == 0
    assert put(ada, url, {"gallery_visible": True}).json()["gallery_visible"] is True
    assert Client().get(f"/e/{event_id}/projects/{w['ada_project'].public_id}/").status_code == 200


def test_only_members_change_visibility_and_only_organizers_block(world):
    w = world
    url = api(w, f"projects/{w['ada_project'].public_id}/visibility/")
    assert put(client_for(w["bob"]), url, {"gallery_visible": False}).status_code == 404
    ada, org = client_for(w["ada"]), client_for(w["org"])
    assert put(ada, url, {"blocked": True, "reason": "x"}).status_code == 400
    assert put(org, url, {"blocked": True}).status_code == 400
    assert (
        put(org, url, {"blocked": True, "reason": "Off-topic"}).json()["blocked_by_organizer"]
        is True
    )
    assert "Ada Bot" not in Client().get(f"/e/{w['event'].public_id}/gallery/").content.decode()
    assert put(ada, url, {"gallery_visible": True}).json()["blocked_by_organizer"] is True
    assert "Ada Bot" not in Client().get(f"/e/{w['event'].public_id}/gallery/").content.decode()
    put(org, url, {"blocked": False})
    assert "Ada Bot" in Client().get(f"/e/{w['event'].public_id}/gallery/").content.decode()
    assert put(ada, url, {}).status_code == 400
    assert put(ada, url, {"gallery_visible": "no"}).status_code == 400
    assert AuditEvent.objects.filter(action="project.visibility_changed").count() >= 3


# CSV preview


CSV = (
    "Title,Owner,Summary,Category,ID\n"
    "Robot,ada,A robot,AI,1\n"
    "Robot,bob,Dup,AI,2\n"
    "Ghost,nobody,x,AI,3\n"
    "Track,ada,x,Nope,4\n"
    ",ada,blank,AI,5\n"
)


def test_csv_preview_suggests_a_mapping_and_reports_row_errors_without_writing(world):
    w = world
    Track.objects.create(event=w["event"], name="AI")
    before = Project.objects.count()
    body = post(
        client_for(w["org"]), api(w, "imports/projects-csv/preview/"), {"csv_text": CSV}
    ).json()
    assert body["suggested_mapping"] == {
        "name": "Title",
        "created_by_username": "Owner",
        "description": "Summary",
        "track": "Category",
        "external_id": "ID",
    }
    assert body["rows"] == 5 and body["importable_rows"] == 1 and body["missing_required"] == []
    messages = {(e["row"], e["field"]): e["message"] for e in body["errors"]}
    assert messages[(3, "name")] == "Duplicate of row 2."
    assert "not in this workspace" in messages[(4, "created_by_username")]
    assert "Unknown track" in messages[(5, "track")] and messages[(6, "name")] == "Name is blank."
    assert body["sample"][0]["name"] == "Robot" and Project.objects.count() == before


def test_csv_preview_honours_an_explicit_mapping_and_flags_missing_columns(world):
    w = world
    org = client_for(w["org"])
    url = api(w, "imports/projects-csv/preview/")
    text = "﻿a,b\nRobot,ada\n"
    mapped = post(
        org, url, {"csv_text": text, "mapping": {"name": "a", "created_by_username": "b"}}
    ).json()
    assert mapped["importable_rows"] == 1
    unmapped = post(org, url, {"csv_text": text}).json()
    assert (
        unmapped["missing_required"] == ["name", "created_by_username"] and unmapped["errors"] == []
    )


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"csv_text": ""},
        {"csv_text": "a,a\n1,2\n"},
        {"csv_text": "a,b\n1,2\n", "mapping": {"name": "zzz"}},
        {"csv_text": "a,b\n1,2\n", "mapping": {"bogus": "a"}},
        {"csv_text": "a,b\n1,2\n", "mapping": {"name": "a", "created_by_username": "a"}},
        {"csv_text": "x" * 1_000_001},
        {"csv_text": "a\n" + "1\n" * 2001},
    ],
)
def test_csv_preview_rejects_bad_input(world, body):
    assert (
        post(
            client_for(world["org"]), api(world, "imports/projects-csv/preview/"), body
        ).status_code
        == 400
    )


def test_csv_preview_is_organizer_only(world):
    assert (
        post(
            client_for(world["ada"]),
            api(world, "imports/projects-csv/preview/"),
            {"csv_text": "a\n1"},
        ).status_code
        == 403
    )


# Participant self-export


def test_a_participant_exports_only_their_own_data(world):
    w = world
    response = client_for(w["ada"]).get(api(w, "my-data/export/"))
    assert response.status_code == 200
    text = response.content.decode()
    assert "ada@example.test" in text or "ada" in text
    assert "bob@example.test" not in text
    stranger = User.objects.create_user(username="stranger")
    assert client_for(stranger).get(api(w, "my-data/export/")).status_code == 403
    assert Client().get(api(w, "my-data/export/")).status_code in (401, 403)
