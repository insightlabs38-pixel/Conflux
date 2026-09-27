import hashlib
import hmac
import json
import socket
from unittest.mock import patch

import pytest
from accounts.models import Session, User
from audit.models import DomainEvent
from django.db import transaction
from django.test import Client
from django.utils import timezone
from events.models import Event
from integrations.models import WebhookDelivery, WebhookSubscription
from integrations.webhooks import (
    MAX_ATTEMPTS,
    deliver_pending,
    envelope,
    send_delivery,
    signed_headers,
    stage_deliveries,
    validate_destination,
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


def test_subscription_is_scoped_and_secret_is_one_time(monkeypatch):
    workspace, event, client = fixture()
    monkeypatch.setattr(socket, "getaddrinfo", public_dns)
    url = base(workspace)
    created = client.post(
        url,
        {
            "url": "https://receiver.example/hook",
            "event": str(event.public_id),
            "event_types": ["event.status_changed"],
        },
        content_type="application/json",
    )
    assert created.status_code == 201
    secret = created.json()["secret"]
    listed = client.get(url).json()
    assert len(listed) == 1 and "secret" not in listed[0]
    other = Workspace.objects.create(name="Other", slug="other-webhook")
    assert client.get(base(other)).status_code == 403
    assert (
        client.patch(
            url + created.json()["public_id"] + "/",
            {"enabled": False},
            content_type="application/json",
        ).status_code
        == 200
    )
    assert secret not in str(WebhookSubscription.objects.values())
    assert Client().get(url).status_code in (401, 403)


def test_unsafe_destination_is_rejected_at_creation_and_delivery(monkeypatch):
    workspace, event, client = fixture()
    for url in (
        "http://example.com/hook",
        "https://127.0.0.1/hook",
        "https://u:p@example.com/hook",
        "https://example.com:444/hook",
    ):
        assert (
            client.post(
                base(workspace),
                {"url": url, "event_types": ["event.status_changed"]},
                content_type="application/json",
            ).status_code
            == 400
        )
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 443))],
    )
    with pytest.raises(ValueError, match="public"):
        validate_destination("https://receiver.example/hook")
    subscription = WebhookSubscription.objects.create(
        workspace=workspace,
        event=event,
        url="https://receiver.example/hook",
        event_types=["event.status_changed"],
    )
    DomainEvent.objects.create(
        workspace=workspace,
        event_type="event.status_changed",
        payload={"event": str(event.public_id)},
    )
    stage_deliveries()
    assert WebhookDelivery.objects.filter(subscription=subscription).count() == 1
    assert deliver_pending() == 1
    delivery = WebhookDelivery.objects.get(subscription=subscription)
    assert delivery.attempts == 1 and delivery.status == WebhookDelivery.Status.PENDING


@pytest.mark.django_db(transaction=True)
def test_outbox_filter_signing_retry_and_replay(monkeypatch):
    workspace, event, client = fixture()
    monkeypatch.setattr(socket, "getaddrinfo", public_dns)
    issued = client.post(
        base(workspace),
        {
            "url": "https://receiver.example/hook",
            "event": str(event.public_id),
            "event_types": ["event.status_changed"],
        },
        content_type="application/json",
    ).json()
    subscription = WebhookSubscription.objects.get(public_id=issued["public_id"])
    other_event = Event.objects.create(workspace=workspace, name="Other", slug="other")
    DomainEvent.objects.create(
        workspace=workspace,
        event_type="event.status_changed",
        payload={"event": str(other_event.public_id)},
    )
    DomainEvent.objects.create(
        workspace=workspace, event_type="event.created", payload={"event": str(event.public_id)}
    )
    matching = DomainEvent.objects.create(
        workspace=workspace,
        event_type="event.status_changed",
        payload={"event": str(event.public_id)},
    )
    assert stage_deliveries() == 1
    assert stage_deliveries() == 0
    delivery = WebhookDelivery.objects.get(subscription=subscription)
    body = json.dumps(envelope(matching), separators=(",", ":"), sort_keys=True).encode()
    headers = signed_headers(subscription, matching, body, timezone.now())
    assert (
        headers["X-Conflux-Signature"]
        == "v1="
        + hmac.new(
            issued["secret"].encode(),
            headers["X-Conflux-Timestamp"].encode() + b"." + body,
            hashlib.sha256,
        ).hexdigest()
    )
    assert (
        hmac.new(
            issued["secret"].encode(),
            headers["X-Conflux-Timestamp"].encode() + b"." + body + b"x",
            hashlib.sha256,
        ).hexdigest()
        != headers["X-Conflux-Signature"][3:]
    )

    def failed_send(*_args):
        assert not transaction.get_connection().in_atomic_block
        return 503

    with patch("integrations.webhooks.send_delivery", side_effect=failed_send) as sender:
        for attempt in range(MAX_ATTEMPTS):
            WebhookDelivery.objects.filter(pk=delivery.pk).update(next_attempt_at=timezone.now())
            assert deliver_pending() == 1
        assert sender.call_count == MAX_ATTEMPTS
    delivery.refresh_from_db()
    assert delivery.status == WebhookDelivery.Status.DEAD
    assert deliver_pending() == 0
    detail = base(workspace) + f"{subscription.public_id}/deliveries/"
    assert client.get(detail).json()[0]["status"] == "dead"
    assert client.post(detail + f"{delivery.public_id}/replay/").status_code == 200
    with patch("integrations.webhooks.send_delivery", return_value=204):
        assert deliver_pending() == 1
    delivery.refresh_from_db()
    assert delivery.status == WebhookDelivery.Status.SUCCEEDED


def test_delivery_pins_resolved_address_and_does_not_follow_redirect(monkeypatch):
    workspace, event, _ = fixture()
    subscription = WebhookSubscription.objects.create(
        workspace=workspace,
        event=event,
        url="https://receiver.example/hook?source=conflux",
        event_types=["event.created"],
    )
    domain_event = DomainEvent.objects.create(
        workspace=workspace,
        event_type="event.created",
        payload={"event": str(event.public_id)},
    )
    monkeypatch.setattr(socket, "getaddrinfo", public_dns)
    captured = []

    class Response:
        status = 302

        def read(self, _limit):
            return b""

    class Connection:
        def __init__(self, host, port, timeout):
            captured.append((host, port, timeout))

        def request(self, method, target, body, headers):
            self._create_connection(("receiver.example", 443), 5, None)
            captured.append((method, target, body, headers))

        def getresponse(self):
            return Response()

        def close(self):
            pass

    monkeypatch.setattr("integrations.webhooks.http.client.HTTPSConnection", Connection)
    monkeypatch.setattr(
        socket, "create_connection", lambda address, timeout, source: captured.append(address)
    )
    assert send_delivery(subscription, domain_event, b"{}") == 302
    assert captured[0] == ("receiver.example", 443, 5)
    assert captured[1] == ("93.184.215.14", 443)
    assert captured[2][0:2] == ("POST", "/hook?source=conflux")
