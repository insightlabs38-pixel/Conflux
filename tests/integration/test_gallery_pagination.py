import re

import pytest
from accounts.models import User
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from events.models import Event, EventStatus, Track
from projects.models import Project, Submission, SubmissionStatus, SubmissionVersion
from stages.models import Stage
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db

COUNT = 55  # more than the default page size (50) and than two HTML pages (24)


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(
        workspace=workspace,
        name="Big",
        slug="big",
        status=EventStatus.OPEN,
        is_public=True,
        starts_at="2026-01-01T00:00:00Z",
        ends_at="2026-01-02T00:00:00Z",
    )
    tracks = [Track.objects.create(event=event, name=n, position=i) for i, n in enumerate("AB")]
    stage = Stage.objects.create(event=event, name="Build", position=0)
    user = User.objects.create_user(username="member", password="unused")
    for n in range(COUNT):
        project = Project.objects.create(
            event=event,
            name=f"Project {n:03d}" if n % 5 else f"Rocket {n:03d}",
            created_by=user,
            track=tracks[n % 2],
        )
        submission = Submission.objects.create(project=project, stage=stage, updated_by=user)
        version = SubmissionVersion.objects.create(
            submission=submission, number=1, snapshot={}, digest="a" * 64, finalized_by=user
        )
        submission.status = SubmissionStatus.FINALIZED
        submission.current_version = version
        submission.save()
    return event, tracks


def api(event, **params):
    return Client().get(f"/api/v1/events/{event.public_id}/gallery/", params)


def names(response):
    return [item["name"] for item in response.json()]


def test_default_page_is_bounded_and_reports_total_and_next_link(world):
    event, _ = world
    response = api(event)
    assert response.status_code == 200
    assert len(response.json()) == 50
    assert response["X-Total-Count"] == str(COUNT)
    assert 'rel="next"' in response["Link"] and "offset=50" in response["Link"]
    assert 'rel="prev"' not in response["Link"]


def test_final_page_has_remainder_and_only_a_prev_link(world):
    event, _ = world
    response = api(event, offset=50)
    assert len(response.json()) == COUNT - 50
    assert 'rel="next"' not in response["Link"] and 'rel="prev"' in response["Link"]


def test_middle_page_has_both_links(world):
    event, _ = world
    response = api(event, limit=10, offset=20)
    assert len(response.json()) == 10
    assert 'rel="next"' in response["Link"] and "offset=30" in response["Link"]
    assert "offset=10" in response["Link"]


def test_pages_partition_the_gallery_in_stable_name_order(world):
    event, _ = world
    walked = names(api(event, limit=20)) + names(api(event, limit=20, offset=20))
    walked += names(api(event, limit=20, offset=40))
    assert walked == sorted(walked) and len(walked) == len(set(walked)) == COUNT
    assert walked == names(api(event, limit=100))


def test_offset_past_the_end_is_an_empty_page_not_an_error(world):
    event, _ = world
    response = api(event, offset=500)
    assert response.status_code == 200 and response.json() == []
    assert response["X-Total-Count"] == str(COUNT)


def test_search_combines_with_paging(world):
    event, _ = world
    first = api(event, q="rocket", limit=5)
    assert first["X-Total-Count"] == "11" and len(first.json()) == 5
    assert all(n.startswith("Rocket") for n in names(first))
    assert "q=rocket" in first["Link"]
    last = api(event, q="rocket", limit=5, offset=10)
    assert len(last.json()) == 1 and 'rel="next"' not in last["Link"]
    empty = api(event, q="zzz-nothing")
    assert empty.json() == [] and empty["X-Total-Count"] == "0"


@pytest.mark.parametrize(
    "params",
    [{"limit": 0}, {"limit": 101}, {"limit": "abc"}, {"offset": -1}, {"offset": "x"}],
)
def test_invalid_or_oversized_paging_is_rejected(world, params):
    event, _ = world
    assert api(event, **params).status_code == 400


def test_hidden_and_blocked_projects_stay_out_of_pages_and_totals(world):
    event, _ = world
    Project.objects.filter(event=event, name="Project 001").update(gallery_visible=False)
    Project.objects.filter(event=event, name="Project 002").update(gallery_blocked=True)
    response = api(event, limit=100)
    assert response["X-Total-Count"] == str(COUNT - 2)
    assert "Project 001" not in names(response) and "Project 002" not in names(response)


def test_query_count_does_not_grow_with_page_size(world):
    event, _ = world
    with CaptureQueriesContext(connection) as small:
        api(event, limit=1)
    with CaptureQueriesContext(connection) as large:
        api(event, limit=100)
    assert len(large) == len(small)


def html(event, **params):
    return Client().get(f"/e/{event.public_id}/gallery/", params).content.decode()


def cards(body):
    return re.findall(r'cx-card__title"><a[^>]*>([^<]+)<', body)


def test_html_gallery_paginates_with_working_next_and_previous_links(world):
    event, _ = world
    page1 = html(event)
    assert len(cards(page1)) == 24 and "Page 1 of 3" in page1 and 'rel="next"' in page1
    assert 'rel="prev"' not in page1
    page3 = html(event, page=3)
    assert len(cards(page3)) == COUNT - 48 and 'rel="next"' not in page3
    assert 'rel="prev"' in page3
    seen = cards(page1) + cards(html(event, page=2)) + cards(page3)
    assert len(set(seen)) == COUNT


def test_html_gallery_tolerates_bad_page_numbers_and_keeps_filters(world):
    event, tracks = world
    assert len(cards(html(event, page="junk"))) == 24
    assert len(cards(html(event, page=99))) == COUNT - 48  # clamps to last page
    filtered = html(event, track=str(tracks[0].public_id), q="rocket", page=1)
    assert all(c.startswith("Rocket") for c in cards(filtered))
    single = html(event, q="zzz-nothing")
    assert "No projects match yet." in single and "cx-pagination" not in single
    body = html(event, q="project")
    assert "q=project&amp;page=2" in body
