"""PD-F003-B01-T02: refusals the completeness contract points at, and the blank-record probe."""

import json

import pytest
from accounts.models import Session, User
from communications.models import Message
from django.core.exceptions import ValidationError
from django.test import Client
from events.models import Announcement, Event, Track
from projects.models import Submission
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="W", slug="w")
    organizer = User.objects.create_user(username="org", password="unused")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    client = Client()
    client.cookies["session"] = Session.issue(organizer).token
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"
    return {"event": event, "client": client, "base": base}


def post(world, path, body):
    return world["client"].post(
        world["base"] + path, data=json.dumps(body), content_type="application/json"
    )


def test_a_track_needs_a_name_and_a_unique_one(world):
    blank = post(world, "tracks/", {"name": ""})
    assert blank.status_code == 400 and "name" in blank.json()
    assert post(world, "tracks/", {"name": "AI"}).status_code == 201
    duplicate = post(world, "tracks/", {"name": "AI"})
    assert duplicate.status_code == 400
    assert Track.objects.filter(event=world["event"]).count() == 1


def test_an_announcement_needs_a_title_and_text_within_bounds(world):
    blank = post(world, "announcements/", {"title": "", "body": "Hello"})
    assert blank.status_code == 400 and "title" in blank.json()
    too_long = post(world, "announcements/", {"title": "T" * 500, "body": "Hello"})
    assert too_long.status_code == 400 and "title" in too_long.json()
    assert Announcement.objects.filter(event=world["event"]).count() == 0


def test_a_message_needs_a_known_audience_and_a_subject_and_leaves_nothing_behind(world):
    unknown = post(
        world,
        "communications/messages/",
        {"subject": "Hi", "body": "Text", "audience_kind": "everyone_on_earth"},
    )
    assert unknown.status_code == 400 and "audience_kind" in unknown.json()
    blank = post(
        world,
        "communications/messages/",
        {"subject": "", "body": "Text", "audience_kind": "all_participants"},
    )
    assert blank.status_code == 400 and "subject" in blank.json()
    assert Message.objects.filter(event=world["event"]).count() == 0


def test_a_blank_submission_is_refused_by_field_validation_instead_of_crashing_clean():
    """Found by the completeness contract: `clean()` read unset relations and raised
    RelatedObjectDoesNotExist for a blank record; now every required part is named."""
    with pytest.raises(ValidationError) as caught:
        Submission().full_clean()
    assert {"project", "stage", "updated_by"} <= set(caught.value.message_dict)
