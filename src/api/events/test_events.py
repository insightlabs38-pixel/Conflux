import json
from datetime import timedelta

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent, DomainEvent
from django.test import Client
from django.utils import timezone
from workspaces.models import Membership, Role, Workspace

from .models import BasePrize, Event, EventStatus, Track

pytestmark = pytest.mark.django_db


def setup_clients():
    organizer = User.objects.create_user(username="organizer", password="unused")
    judge = User.objects.create_user(username="judge", password="unused")
    workspace = Workspace.objects.create(name="Workspace", slug="workspace")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    organizer_client = Client()
    organizer_client.cookies["session"] = Session.issue(organizer).token
    judge_client = Client()
    judge_client.cookies["session"] = Session.issue(judge).token
    return workspace, organizer_client, judge_client


def url(workspace, suffix=""):
    return f"/workspaces/{workspace.public_id}/events/{suffix}"


def payload(name="Example"):
    return {
        "name": name,
        "slug": name.lower(),
        "timezone": "America/New_York",
        "starts_at": (timezone.now() + timedelta(days=1)).isoformat(),
        "ends_at": (timezone.now() + timedelta(days=2)).isoformat(),
    }


def post(client, path, data):
    return client.post(path, data=json.dumps(data), content_type="application/json")


def patch(client, path, data):
    return client.patch(path, data=json.dumps(data), content_type="application/json")


def test_nonexistent_workspace_id_is_not_found():
    _, client, _ = setup_clients()
    response = client.get("/workspaces/00000000-0000-0000-0000-000000000000/events/")
    assert response.status_code == 404


def test_event_lifecycle_and_audit():
    workspace, client, judge = setup_clients()
    base = url(workspace)
    assert judge.get(base).status_code == 403
    assert Client().get(base).status_code == 401
    created = post(client, base, payload())
    assert created.status_code == 201, created.content
    event_id = created.json()["public_id"]
    detail = f"{base}{event_id}/"
    assert client.get(base).json()[0]["public_id"] == event_id
    assert client.get(detail).status_code == 200
    assert judge.get(detail).status_code == 403
    assert patch(client, detail, {"name": "Renamed"}).json()["name"] == "Renamed"
    assert post(client, detail + "status/", {"status": "closed"}).status_code == 400
    for state in ("open", "closed", "archived"):
        result = post(client, detail + "status/", {"status": state})
        assert result.status_code == 200, result.content
        assert result.json()["status"] == state
    assert patch(client, detail, {"name": "Too late"}).status_code == 400
    assert client.delete(detail).status_code == 400
    assert AuditEvent.objects.filter(workspace=workspace).count() == 5
    assert DomainEvent.objects.filter(workspace=workspace).count() == 5


def test_event_validation_and_tenant_scope():
    workspace, client, _ = setup_clients()
    base = url(workspace)
    assert post(client, base, {**payload(), "timezone": "Atlantis/Nowhere"}).status_code == 400
    dates = payload()
    dates["ends_at"] = dates["starts_at"]
    assert post(client, base, dates).status_code == 400
    created = post(client, base, payload())
    assert created.status_code == 201
    assert post(client, base, payload()).status_code == 400
    event_id = created.json()["public_id"]
    other = Workspace.objects.create(name="Other", slug="other")
    assert client.get(url(other, f"{event_id}/")).status_code == 403
    assert post(client, base, {"name": "No dates", "slug": "no-dates"}).status_code == 201
    undated = Event.objects.get(slug="no-dates")
    assert (
        post(client, url(workspace, f"{undated.public_id}/status/"), {"status": "open"}).status_code
        == 400
    )
    assert undated.status == EventStatus.DRAFT


def test_tracks_prizes_and_dashboard():
    workspace, client, _ = setup_clients()
    event_id = post(client, url(workspace), payload()).json()["public_id"]
    base = url(workspace, f"{event_id}/")
    dashboard = client.get(base + "dashboard/").json()
    assert len(dashboard["configuration_checks"]) == 2
    track = post(client, base + "tracks/", {"name": "AI", "position": 1})
    assert track.status_code == 201, track.content
    track_id = track.json()["public_id"]
    assert post(client, base + "tracks/", {"name": "AI"}).status_code == 400
    prize = post(
        client,
        base + "base-prizes/",
        {"name": "First", "kind": "cash", "amount": "500.00", "currency": "USD", "track": track_id},
    )
    assert prize.status_code == 201, prize.content
    prize_id = prize.json()["public_id"]
    assert prize.json()["track"] == track_id
    assert (
        post(
            client, base + "base-prizes/", {"name": "Bad", "kind": "hardware", "amount": "10"}
        ).status_code
        == 400
    )
    assert client.get(base + "dashboard/").json()["configuration_checks"] == []
    assert patch(client, base + f"base-prizes/{prize_id}/", {"amount": "750.00"}).status_code == 200
    assert client.delete(base + f"tracks/{track_id}/").status_code == 204
    assert BasePrize.objects.get(public_id=prize_id).track is None
    assert Track.objects.count() == 0


def test_public_visibility_and_draft_deletion():
    workspace, client, _ = setup_clients()
    created = post(client, url(workspace), {**payload(), "is_public": True})
    event_id = created.json()["public_id"]
    public_path = f"/events/{event_id}/"
    assert Client().get(public_path).status_code == 404
    detail = url(workspace, f"{event_id}/")
    assert post(client, detail + "status/", {"status": "open"}).status_code == 200
    public = Client().get(public_path)
    assert public.status_code == 200
    assert public.json()["name"] == "Example"
    assert "is_public" not in public.json()
    assert post(client, detail + "status/", {"status": "closed"}).status_code == 200
    assert Client().get(public_path).status_code == 404
    assert client.delete(detail).status_code == 400
    draft = post(client, url(workspace), {"name": "Disposable", "slug": "disposable"})
    assert client.delete(url(workspace, draft.json()["public_id"] + "/")).status_code == 204
    assert not Event.objects.filter(slug="disposable").exists()


def test_prize_track_must_belong_to_event():
    workspace, client, _ = setup_clients()
    first = post(client, url(workspace), payload("First")).json()["public_id"]
    second = post(client, url(workspace), payload("Second")).json()["public_id"]
    foreign_track = post(client, url(workspace, first + "/tracks/"), {"name": "Foreign"}).json()[
        "public_id"
    ]
    second_prizes = url(workspace, second + "/base-prizes/")
    response = post(
        client, second_prizes, {"name": "Wrong", "kind": "other", "track": foreign_track}
    )
    assert response.status_code == 404
    assert BasePrize.objects.count() == 0
