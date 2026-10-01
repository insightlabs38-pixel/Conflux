"""PD-F002-B01-T06: sending a message is the first operation to adopt the approval gate."""

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from communications.models import Message
from core import approvals
from core.models import ApprovalRequest
from django.core import mail
from django.test import Client
from events.models import Event
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

MESSAGE = {"subject": "Welcome", "body": "Good luck!", "audience_kind": "all_participants"}


@pytest.fixture
def case():
    workspace = Workspace.objects.create(name="M", slug="m")
    users = {}
    for name, role in (
        ("org", Role.ORGANIZER),
        ("org2", Role.ORGANIZER),
        ("p1", Role.PARTICIPANT),
        ("p2", Role.PARTICIPANT),
    ):
        users[name] = User.objects.create_user(
            username=name, password="unused", email=f"{name}@example.com"
        )
        Membership.objects.create(user=users[name], workspace=workspace, role=role)
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    clients = {}
    for name, user in users.items():
        c = Client()
        c.cookies["session"] = Session.issue(user).token
        clients[name] = c
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"
    return {"event": event, "users": users, "client": clients, "base": base}


def send(case, who="org", **over):
    return case["client"][who].post(
        case["base"] + "communications/messages/",
        data={**MESSAGE, **over},
        content_type="application/json",
    )


def bulk(case, token=None, **over):
    op = {"action": "send", **MESSAGE, **over}
    body = {"operations": [op], **({"preview_token": token} if token else {})}
    return case["client"]["org"].post(
        case["base"] + "operations/bulk/", data=body, content_type="application/json"
    )


def enable(case):
    response = case["client"]["org"].put(
        case["base"] + "approval-gates/message_send/",
        data={"enabled": True},
        content_type="application/json",
    )
    assert response.status_code == 200 and response.json()["enabled"] is True


def approve(case, approval_id, who="org2"):
    return case["client"][who].post(
        case["base"] + f"approvals/{approval_id}/decision/",
        data={"decision": "approve", "note": "ok"},
        content_type="application/json",
    )


def test_a_message_goes_out_as_before_when_the_gate_is_off(case):
    assert send(case).status_code == 201
    assert Message.objects.count() == 1 and not ApprovalRequest.objects.exists()


def test_with_the_gate_on_a_message_waits_for_another_organizer(case):
    enable(case)
    held = send(case)
    assert held.status_code == 409
    body = held.json()
    assert body["code"] == "approval_required"
    approval = body["approval"]
    assert approval["status"] == "pending" and approval["can_decide"] is False
    assert approval["summary"][0] == "Send “Welcome” to 2 people."
    assert "Good luck!" in approval["summary"][2]
    # Nothing was sent, delivered or recorded as sent while it waits.
    assert not Message.objects.exists() and mail.outbox == []
    assert not AuditEvent.objects.filter(action="message.sent").exists()

    # The sender cannot approve it; another organizer can; a participant cannot see it.
    assert approve(case, approval["public_id"], "org").status_code == 400
    assert approve(case, approval["public_id"], "p1").status_code == 404
    assert approve(case, approval["public_id"]).json()["status"] == "approved"

    sent = send(case)
    assert sent.status_code == 201 and sent.json()["recipient_count"] == 2
    assert len(mail.outbox) == 2
    assert ApprovalRequest.objects.get().status == "executed"
    # Spent: the same message again needs a new approval.
    assert send(case).status_code == 409
    # A different body is a different message and needs its own.
    assert send(case, body="Something else").status_code == 409
    assert ApprovalRequest.objects.count() == 3


def test_the_bulk_planner_shows_the_need_in_the_preview_and_holds_the_apply(case):
    enable(case)
    preview = bulk(case)
    assert preview.status_code == 200
    shown = preview.json()
    assert shown["applied"] is False and shown["approvals"][0]["action"] == "message_send"
    assert shown["effects"][0]["recipient_count"] == 2
    assert not ApprovalRequest.objects.exists()  # a preview opens nothing

    held = bulk(case, shown["preview_token"])
    assert held.status_code == 409 and held.json()["code"] == "approval_required"
    assert not Message.objects.exists()
    approval_id = held.json()["approval"]["public_id"]
    assert approve(case, approval_id).status_code == 200

    done = bulk(case, shown["preview_token"])
    assert done.status_code == 200 and done.json()["applied"] is True
    assert Message.objects.count() == 1
    assert ApprovalRequest.objects.get().status == "executed"
    # Retrying the same token replays the receipt; it does not ask for a second approval.
    assert bulk(case, shown["preview_token"]).json() == done.json()


def test_one_approval_covers_the_message_whichever_door_it_came_through(case):
    enable(case)
    held = send(case)
    approve(case, held.json()["approval"]["public_id"])
    preview = bulk(case).json()
    assert bulk(case, preview["preview_token"]).status_code == 200  # same content, same digest
    assert Message.objects.count() == 1


def test_a_preview_without_the_gate_has_no_approvals_entry(case):
    assert "approvals" not in bulk(case).json()


def test_turning_the_gate_off_again_lets_messages_through(case):
    enable(case)
    assert send(case).status_code == 409
    case["client"]["org"].put(
        case["base"] + "approval-gates/message_send/",
        data={"enabled": False},
        content_type="application/json",
    )
    assert send(case).status_code == 201
    assert approvals.gate_enabled(case["event"], "message_send") is False
