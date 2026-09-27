import pytest
from accounts.models import Session, User
from communications.models import Message, MessageRecipient
from django.core import mail
from django.test import Client
from events.models import Event
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def fixture():
    organizer = User.objects.create_user(username="msg-organizer", password="unused")
    with_email = User.objects.create_user(
        username="msg-participant", password="unused", email="participant@example.com"
    )
    no_email = User.objects.create_user(username="msg-participant-2", password="unused")
    workspace = Workspace.objects.create(name="Messaging", slug="messaging")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=with_email, workspace=workspace, role=Role.PARTICIPANT)
    Membership.objects.create(user=no_email, workspace=workspace, role=Role.PARTICIPANT)
    event = Event.objects.create(workspace=workspace, name="Event", slug="event")
    return workspace, event, organizer, with_email, no_email


def messages_url(workspace, event):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        "/communications/messages/"
    )


def test_sending_a_message_delivers_in_app_and_best_effort_email():
    workspace, event, organizer, with_email, no_email = fixture()
    client = Client()
    client.cookies["session"] = Session.issue(organizer).token

    response = client.post(
        messages_url(workspace, event),
        {
            "subject": "Welcome",
            "body": "Good luck at the event!",
            "audience_kind": "all_participants",
        },
        content_type="application/json",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["recipient_count"] == 2

    message = Message.objects.get(public_id=body["public_id"])
    recipients = MessageRecipient.objects.filter(message=message)
    assert recipients.count() == 2
    with_email_row = recipients.get(user=with_email)
    no_email_row = recipients.get(user=no_email)
    assert with_email_row.email_sent_at is not None
    assert with_email_row.email_error == ""
    assert no_email_row.email_sent_at is None

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["participant@example.com"]
    assert mail.outbox[0].subject == "Welcome"

    listed = client.get(messages_url(workspace, event)).json()
    assert listed[0]["subject"] == "Welcome"


def test_recipient_reads_and_marks_inbox_message():
    workspace, event, organizer, with_email, no_email = fixture()
    organizer_client = Client()
    organizer_client.cookies["session"] = Session.issue(organizer).token
    organizer_client.post(
        messages_url(workspace, event),
        {"subject": "Reminder", "body": "Submit soon.", "audience_kind": "all_participants"},
        content_type="application/json",
    )

    participant_client = Client()
    participant_client.cookies["session"] = Session.issue(no_email).token
    inbox_url = f"/api/v1/workspaces/{workspace.public_id}/inbox/"
    inbox = participant_client.get(inbox_url).json()
    assert len(inbox) == 1
    assert inbox[0]["subject"] == "Reminder"
    assert inbox[0]["read_at"] is None

    recipient = MessageRecipient.objects.get(user=no_email)
    read = participant_client.post(f"{inbox_url}{recipient.public_id}/read/")
    assert read.status_code == 200
    assert read.json()["read_at"] is not None

    other_client = Client()
    other_client.cookies["session"] = Session.issue(with_email).token
    denied = other_client.post(f"{inbox_url}{recipient.public_id}/read/")
    assert denied.status_code == 400
