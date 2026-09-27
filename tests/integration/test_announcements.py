import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Announcement, Event, EventStatus
from presentation.models import Page, PageBlock
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client(user):
    result = Client()
    result.cookies["session"] = Session.issue(user).token
    return result


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
        status=EventStatus.OPEN,
        is_public=True,
        starts_at="2027-01-01T00:00:00Z",
        ends_at="2027-01-02T00:00:00Z",
    )
    return workspace, organizer, participant, event


def url(workspace, event, suffix=""):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/announcements/{suffix}"
    )


def test_organizer_manages_announcements_and_others_cannot():
    workspace, organizer, participant, event = fixture()
    announcements_url = url(workspace, event)
    assert (
        client(participant)
        .post(
            announcements_url,
            {"title": "Lunch", "body": "Pizza at noon"},
            content_type="application/json",
        )
        .status_code
        == 403
    )

    created = client(organizer).post(
        announcements_url,
        {"title": "Lunch", "body": "Pizza at noon"},
        content_type="application/json",
    )
    assert created.status_code == 201
    assert created.json()["posted_by"] == "organizer"

    listed = client(organizer).get(announcements_url).json()
    assert len(listed) == 1
    assert client(participant).get(announcements_url).status_code == 403

    announcement_id = listed[0]["public_id"]
    assert (
        client(participant).delete(url(workspace, event, f"{announcement_id}/")).status_code == 403
    )
    assert client(organizer).delete(url(workspace, event, f"{announcement_id}/")).status_code == 204
    assert Announcement.objects.filter(event=event).count() == 0


def test_public_site_renders_recent_announcements():
    workspace, organizer, participant, event = fixture()
    Announcement.objects.create(
        event=event, title="Kickoff", body="Doors open at 9am.", posted_by=organizer
    )
    page = Page.objects.create(event=event)
    PageBlock.objects.create(page=page, kind="announcements", position=0, config={})

    html_response = Client().get(f"/e/{event.public_id}/")
    assert html_response.status_code == 200
    body = html_response.content.decode()
    assert "Kickoff" in body
    assert "Doors open at 9am." in body
    assert 'rel="manifest"' in body


def test_service_worker_is_served_under_the_site_path_for_full_scope():
    response = Client().get("/e/sw.js")
    assert response.status_code == 200
    assert response["Content-Type"] == "application/javascript"
    assert b"caches.open" in response.content
