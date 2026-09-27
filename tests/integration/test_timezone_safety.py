from datetime import UTC, datetime

import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
from policies.timezone_safety import dst_warning, local_iso
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def utc(*args):
    return datetime(*args, tzinfo=UTC)


# US spring-forward in 2026: clocks jump 02:00 -> 03:00 America/New_York
# at 2026-03-08 07:00 UTC (EST -05:00 becomes EDT -04:00).
SPRING_FORWARD_UTC = utc(2026, 3, 8, 7, 0)


def test_dst_warning_fires_only_when_the_window_spans_a_real_transition():
    spanning = dst_warning(utc(2026, 3, 8, 5, 0), utc(2026, 3, 8, 12, 0), "America/New_York")
    assert spanning is not None
    assert "-05:00" in spanning
    assert "-04:00" in spanning

    not_spanning = dst_warning(utc(2026, 3, 8, 13, 0), utc(2026, 3, 8, 15, 0), "America/New_York")
    assert not_spanning is None

    assert dst_warning(None, utc(2026, 3, 8, 12, 0), "America/New_York") is None


def test_local_iso_reflects_the_correct_offset_on_either_side_of_the_transition():
    before = local_iso(utc(2026, 3, 8, 6, 0), "America/New_York")
    after = local_iso(utc(2026, 3, 8, 8, 0), "America/New_York")
    assert before.endswith("-05:00")
    assert after.endswith("-04:00")
    assert local_iso(None, "America/New_York") is None


def fixture():
    workspace = Workspace.objects.create(name="One", slug="one")
    organizer = User.objects.create_user(username="organizer")
    participant = User.objects.create_user(username="participant")
    Membership.objects.create(workspace=workspace, user=organizer, role=Role.ORGANIZER)
    Membership.objects.create(workspace=workspace, user=participant, role=Role.PARTICIPANT)
    event = Event.objects.create(
        workspace=workspace,
        name="Hack",
        slug="hack",
        timezone="America/New_York",
        starts_at=utc(2026, 3, 8, 5, 0),
        ends_at=utc(2026, 3, 9, 5, 0),
    )
    return workspace, organizer, participant, event


def gates_url(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/temporal-gates/"


def timeline_url(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/timezone-timeline/"


def test_temporal_gate_api_exposes_local_time_and_dst_warning():
    workspace, organizer, participant, event = fixture()
    created = client_for(organizer).post(
        gates_url(workspace, event),
        {
            "name": "Submissions",
            "opens_at": "2026-03-08T05:00:00Z",
            "closes_at": "2026-03-08T12:00:00Z",
        },
        content_type="application/json",
    )
    assert created.status_code == 201
    body = created.json()
    assert body["event_local_opens_at"].endswith("-05:00")
    assert body["event_local_closes_at"].endswith("-04:00")
    assert body["dst_warning"] is not None


def test_timezone_timeline_lists_event_window_and_gates_chronologically():
    workspace, organizer, participant, event = fixture()
    client_for(organizer).post(
        gates_url(workspace, event),
        {
            "name": "Submissions",
            "opens_at": "2026-03-08T13:00:00Z",
            "closes_at": "2026-03-08T15:00:00Z",
        },
        content_type="application/json",
    )
    assert client_for(participant).get(timeline_url(workspace, event)).status_code == 403

    response = client_for(organizer).get(timeline_url(workspace, event))
    assert response.status_code == 200
    body = response.json()
    labels = [item["label"] for item in body]
    assert labels == ["Event window", "Submissions"]
    event_window = body[0]
    assert event_window["dst_warning"] is not None
    submissions = body[1]
    assert submissions["dst_warning"] is None
