from datetime import timedelta

import pytest
from accounts.models import Session, User
from communications.models import Message, MessageRecipient, Reminder
from communications.reminders import dispatch_due_reminders
from django.test import Client
from django.utils import timezone
from events.models import Event, Track
from participation.models import Team, TeamMembership
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def setup_case():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    organizer = User.objects.create_user(username="organizer", password="unused")
    participant = User.objects.create_user(username="participant", password="unused")
    Membership.objects.create(workspace=workspace, user=organizer, role=Role.ORGANIZER)
    Membership.objects.create(workspace=workspace, user=participant, role=Role.PARTICIPANT)
    client = Client()
    client.cookies["session"] = Session.issue(organizer).token
    endpoint = (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        "/communications/reminders/"
    )
    return event, organizer, participant, client, endpoint


def schedule(
    client, endpoint, *, due_at=None, kind="deadline", audience="all_participants", params=None
):
    return client.post(
        endpoint,
        {
            "kind": kind,
            "due_at": (due_at or timezone.now() + timedelta(hours=1)).isoformat(),
            "audience_kind": audience,
            "audience_params": params or {},
            "subject": "Reminder",
            "body": "Please finish your work.",
        },
        content_type="application/json",
    )


def test_due_reminder_resolves_live_recipients_once_into_local_inbox():
    event, _, participant, client, endpoint = setup_case()
    response = schedule(client, endpoint, audience="unteamed_participants")
    assert response.status_code == 201
    reminder = Reminder.objects.get(public_id=response.json()["public_id"])
    assert dispatch_due_reminders(at=reminder.due_at - timedelta(seconds=1)) == 0
    team = Team.objects.create(event=event, name="Joined")
    TeamMembership.objects.create(team=team, user=participant)
    assert dispatch_due_reminders(at=reminder.due_at) == 1
    reminder.refresh_from_db()
    assert reminder.sent_message_id is not None
    assert reminder.sent_message.recipient_count == 0
    assert dispatch_due_reminders(at=reminder.due_at + timedelta(minutes=1)) == 0
    assert Message.objects.count() == 1


def test_judging_and_voting_reminders_can_target_existing_audiences():
    event, _, participant, client, endpoint = setup_case()
    judging = schedule(client, endpoint, kind="judging", audience="all_judges")
    voting = schedule(client, endpoint, kind="voting")
    assert judging.status_code == voting.status_code == 201
    assert dispatch_due_reminders(at=timezone.now() + timedelta(hours=2)) == 2
    assert MessageRecipient.objects.count() == 1
    assert MessageRecipient.objects.get().user_id == participant.id


def test_cancelled_reminder_never_sends_and_sent_reminder_cannot_cancel():
    _, _, _, client, endpoint = setup_case()
    first = schedule(client, endpoint).json()["public_id"]
    cancelled = client.post(endpoint + f"{first}/cancel/")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert dispatch_due_reminders(at=timezone.now() + timedelta(hours=2)) == 0
    second = schedule(client, endpoint).json()["public_id"]
    assert dispatch_due_reminders(at=timezone.now() + timedelta(hours=2)) == 1
    assert client.post(endpoint + f"{second}/cancel/").status_code == 400


def test_invalid_schedule_and_non_organizer_are_rejected():
    event, _, participant, client, endpoint = setup_case()
    assert (
        schedule(client, endpoint, due_at=timezone.now() - timedelta(minutes=1)).status_code == 400
    )
    assert schedule(client, endpoint, audience="unknown").status_code == 400
    judge_client = Client()
    judge_client.cookies["session"] = Session.issue(participant).token
    assert schedule(judge_client, endpoint).status_code == 403
    assert judge_client.get(endpoint).status_code == 403
    assert event.reminders.count() == 0


def test_invalidated_audience_retries_without_persisting_a_partial_message():
    event, _, _, client, endpoint = setup_case()
    track = Track.objects.create(event=event, name="T")
    response = schedule(
        client, endpoint, audience="track_participants", params={"track": str(track.public_id)}
    )
    assert response.status_code == 201
    reminder = Reminder.objects.get(public_id=response.json()["public_id"])
    track.delete()
    assert dispatch_due_reminders(at=reminder.due_at) == 0
    reminder.refresh_from_db()
    assert reminder.sent_message_id is None
    assert reminder.retry_after > reminder.due_at
    assert "Track not found" in reminder.last_error
    assert Message.objects.count() == 0


def test_revoked_organizer_cannot_send_a_scheduled_reminder():
    event, organizer, _, client, endpoint = setup_case()
    response = schedule(client, endpoint)
    reminder = Reminder.objects.get(public_id=response.json()["public_id"])
    Membership.objects.filter(workspace=event.workspace, user=organizer).delete()
    assert dispatch_due_reminders(at=reminder.due_at) == 0
    reminder.refresh_from_db()
    assert reminder.sent_message_id is None
    assert "no longer has permission" in reminder.last_error
    assert Message.objects.count() == 0
