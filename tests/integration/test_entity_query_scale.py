"""PD-F006-B01-T07: the entity query pages a large event correctly and without per-row queries."""

import time

import pytest
from accounts.models import Session, User
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from events.models import Event, Track
from projects.models import Project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

TOTAL = 5012  # the Wide-1920 stress fixture of design/organizer-data-surface


def world():
    organizer = User.objects.create_user(username="org", password="unused")
    workspace = Workspace.objects.create(name="S", slug="s")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    tracks = [Track.objects.create(event=event, name=f"Track {i}") for i in range(9)]
    Project.objects.bulk_create(
        [
            Project(
                event=event,
                track=tracks[i % 9],
                name=f"Project {i:05d}",
                description="needle" if i % 500 == 0 else "",
                created_by=organizer,
            )
            for i in range(TOTAL)
        ]
    )
    client = Client()
    client.cookies["session"] = Session.issue(organizer).token
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/entities/projects/"
    return client, base


def test_a_large_event_pages_exactly_with_a_counted_total_and_no_per_row_queries():
    client, base = world()
    with CaptureQueriesContext(connection) as queries:
        started = time.perf_counter()
        first = client.get(base, {"sort": "name", "limit": 100}).json()
        elapsed = time.perf_counter() - started
    assert first["total"] == TOTAL and len(first["rows"]) == 100
    assert first["rows"][0]["name"] == "Project 00000"
    with CaptureQueriesContext(connection) as small:
        client.get(base, {"sort": "name", "limit": 25})
    assert len(queries) == len(small)  # the number of queries does not grow with the rows
    assert elapsed < 2.0  # a pathology guard, not a benchmark

    last = client.get(base, {"sort": "name", "limit": 100, "offset": 5000}).json()
    assert len(last["rows"]) == 12 and last["rows"][-1]["name"] == f"Project {TOTAL - 1:05d}"
    past = client.get(base, {"limit": 100, "offset": 6000}).json()
    assert past["rows"] == [] and past["total"] == TOTAL  # the client lands on the last page

    names = []
    for offset in range(0, 300, 50):  # pages never overlap or skip, whatever the page size
        names += [
            r["name"]
            for r in client.get(base, {"sort": "-name", "limit": 50, "offset": offset}).json()[
                "rows"
            ]
        ]
    assert names == sorted(set(names), reverse=True) and len(names) == 300


def test_search_and_filter_count_exactly_on_a_large_event():
    client, base = world()
    found = client.get(base, {"search": "needle", "limit": 25}).json()
    assert found["total"] == len(range(0, TOTAL, 500)) and found["search"] == "needle"
    mixed = client.get(
        base, {"search": "needle", "filter": '{"field":"track","op":"eq","value":"Track 0"}'}
    ).json()
    assert mixed["total"] == sum(1 for i in range(0, TOTAL, 500) if i % 9 == 0)
