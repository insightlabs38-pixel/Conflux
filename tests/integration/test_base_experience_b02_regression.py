"""PD-F001-B02-T90: cross-cutting proofs for generated configuration and consequences.

Both are read-only answers about shared state. This checks what cuts across them: reading never
writes, answers are deterministic, old and archived events are handled, and an answer that goes
stale before the operation runs is corrected by the operation's own validation.
"""

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent, DomainEvent
from django.test import Client
from eventconfig.consequences import ACTIONS
from eventconfig.models import EventModuleSetting, EventProfile
from events.models import BasePrize, Event, EventStatus, Track
from stages.models import Stage, StageEntry, StageTransition
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def world():
    organizer = User.objects.create_user(username="org", password="unused")
    workspace = Workspace.objects.create(name="B02", slug="b02")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    client = Client()
    client.cookies["session"] = Session.issue(organizer).token
    root = f"/api/v1/workspaces/{workspace.public_id}/"
    made = client.post(
        root + "event-templates/library/hackathon/instantiate/",
        data={"name": "Spring", "starts_at": "2027-03-05T09:00:00Z"},
        content_type="application/json",
    )
    assert made.status_code == 201, made.content
    event = Event.objects.get(workspace=workspace)
    return workspace, client, root, root + f"events/{event.public_id}/", event


def counts():
    return (
        AuditEvent.objects.count(),
        DomainEvent.objects.count(),
        Event.objects.count(),
        Stage.objects.count(),
        StageTransition.objects.count(),
        Track.objects.count(),
        BasePrize.objects.count(),
        EventProfile.objects.count(),
        EventModuleSetting.objects.count(),
    )


def targets(event):
    build = Stage.objects.get(event=event, name="Build")
    link = StageTransition.objects.get(from_stage=build)
    return {
        "event.open": None,
        "event.close": None,
        "event.archive": None,
        "event.delete": None,
        "stage.delete": build,
        "stage_transition.delete": link,
        "track.delete": Track.objects.create(event=event, name="Hardware"),
        "base_prize.delete": BasePrize.objects.create(event=event, name="Prize"),
    }


def test_previewing_every_action_and_generating_configuration_never_writes():
    _, client, _, base, event = world()
    chosen = targets(event)
    assert set(chosen) == set(ACTIONS)
    before = counts()
    for action, target in chosen.items():
        suffix = f"&target={target.public_id}" if target else ""
        response = client.get(base + f"consequences/?action={action}{suffix}")
        assert response.status_code == 200, (action, response.content)
    assert client.get(base + "configuration/generated/").status_code == 200
    assert counts() == before
    # The rolled-back graph check left every link where it was.
    assert StageTransition.objects.filter(from_stage__event=event).count() == 2


def test_the_answers_are_deterministic():
    _, client, _, base, event = world()
    first = client.get(base + "configuration/generated/").json()
    assert client.get(base + "configuration/generated/").json() == first
    url = base + "consequences/?action=event.open"
    assert client.get(url).json() == client.get(url).json()


def test_a_preview_that_went_stale_is_corrected_by_the_operation_itself():
    _, client, _, base, event = world()
    build = Stage.objects.get(event=event, name="Build")
    shown = client.get(base + f"consequences/?action=stage.delete&target={build.public_id}").json()
    assert shown["allowed"] is True
    # Someone enters the stage after the dialog was opened: the endpoint still refuses.
    StageEntry.objects.create(stage=build, subject_type="project", subject_id="1")
    response = client.delete(base + f"stages/{build.public_id}/")
    assert response.status_code == 400 and Stage.objects.filter(pk=build.pk).exists()
    assert "ever held a participant" in response.json()["detail"]


def test_an_event_that_predates_the_slice_and_an_archived_one_are_handled():
    workspace, client, root, _, _ = world()
    legacy = Event.objects.create(workspace=workspace, name="Legacy", slug="legacy")
    Stage.objects.create(event=legacy, name="Only", is_initial=True)
    base = root + f"events/{legacy.public_id}/"
    generated = client.get(base + "configuration/generated/").json()
    assert generated["preset"] is None and generated["document"]["format"] is None
    assert client.get(base + "consequences/?action=event.open").status_code == 200
    assert not EventProfile.objects.filter(event=legacy).exists()

    Event.objects.filter(pk=legacy.pk).update(status=EventStatus.ARCHIVED)
    archived = client.get(base + "configuration/generated/").json()
    # An archived event is read-only but its configuration is still stated.
    assert "event.name" in {e["key"] for e in archived["explicit"]}
    shown = client.get(base + "consequences/?action=event.archive").json()
    assert shown["allowed"] is False and shown["refusal"]["code"] == "invalid_transition"
    track = Track.objects.create(event=legacy, name="Late")
    response = client.delete(base + f"tracks/{track.public_id}/")
    assert response.status_code == 400  # archived events cannot be edited
    assert Track.objects.filter(pk=track.pk).exists()
