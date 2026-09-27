import json
import socket
from unittest.mock import patch

import pytest
from accounts.models import Session, User
from audit.models import DomainEvent
from django.test import Client
from events.models import Event
from integrations.models import WebhookSubscription
from integrations.webhooks import (
    chat_summary,
    deliver_pending,
    envelope,
    payload_for,
    stage_deliveries,
)
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def fixture():
    organizer = User.objects.create_user(username="webhook-organizer", password="unused")
    workspace = Workspace.objects.create(name="Webhook workspace", slug="webhook-workspace")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="Event", slug="event")
    client = Client()
    client.cookies["session"] = Session.issue(organizer).token
    return workspace, event, client


def base(workspace):
    return f"/api/v1/workspaces/{workspace.public_id}/webhooks/"


def public_dns(*args, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", 443))]


def test_chat_summary_humanizes_the_type_and_renders_only_scalar_fields():
    workspace, event, _ = fixture()
    domain_event = DomainEvent.objects.create(
        workspace=workspace,
        event_type="event.status_changed",
        payload={"event": str(event.public_id), "status": "open", "nested": {"a": 1}},
    )
    summary = chat_summary(domain_event)
    assert summary == "Conflux — event status changed (status: open)"


def test_payload_for_selects_the_right_shape_per_platform():
    workspace, event, _ = fixture()
    domain_event = DomainEvent.objects.create(
        workspace=workspace, event_type="event.created", payload={"event": str(event.public_id)}
    )
    generic = WebhookSubscription.objects.create(
        workspace=workspace, url="https://receiver.example/hook", event_types=["event.created"]
    )
    discord = WebhookSubscription.objects.create(
        workspace=workspace,
        url="https://discord.com/api/webhooks/1/token",
        event_types=["event.created"],
        platform="discord",
    )
    slack = WebhookSubscription.objects.create(
        workspace=workspace,
        url="https://hooks.slack.com/services/1/2/3",
        event_types=["event.created"],
        platform="slack",
    )
    assert payload_for(generic, domain_event) == envelope(domain_event)
    assert payload_for(discord, domain_event) == {"content": chat_summary(domain_event)}
    assert payload_for(slack, domain_event) == {"text": chat_summary(domain_event)}


def test_a_discord_subscription_delivers_a_content_body_end_to_end(monkeypatch):
    workspace, event, client = fixture()
    monkeypatch.setattr(socket, "getaddrinfo", public_dns)
    created = client.post(
        base(workspace),
        {
            "url": "https://discord.com/api/webhooks/1/token",
            "event": str(event.public_id),
            "event_types": ["event.status_changed"],
            "platform": "discord",
        },
        content_type="application/json",
    )
    assert created.status_code == 201
    assert created.json()["platform"] == "discord"

    DomainEvent.objects.create(
        workspace=workspace,
        event_type="event.status_changed",
        payload={"event": str(event.public_id), "status": "open"},
    )
    stage_deliveries()
    with patch("integrations.webhooks.send_delivery") as sender:
        sender.return_value = 204
        assert deliver_pending() == 1
    sent_body = sender.call_args.args[2]
    assert json.loads(sent_body) == {"content": "Conflux — event status changed (status: open)"}
