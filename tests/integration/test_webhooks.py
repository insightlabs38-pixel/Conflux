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
from integrations.models import WebhookAttempt, WebhookDelivery, WebhookSubscription
from integrations.webhooks import (
    MAX_ATTEMPTS,
    deliver_pending,
    envelope,
    send_delivery,
    signed_headers,
    signing_secret,
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

    def failed_send(*_args, headers):
        assert not transaction.get_connection().in_atomic_block
        assert headers["X-Conflux-Event-Id"] == str(matching.public_id)
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


def inspected_delivery():
    workspace, event, client = fixture()
    subscription = WebhookSubscription.objects.create(
        workspace=workspace,
        event=event,
        url="https://receiver.example/hook",
        event_types=["event.status_changed"],
    )
    domain_event = DomainEvent.objects.create(
        workspace=workspace,
        event_type="event.status_changed",
        payload={"event": str(event.public_id), "name": "Café <script>"},
    )
    delivery = WebhookDelivery.objects.create(subscription=subscription, domain_event=domain_event)
    url = base(workspace) + f"{subscription.public_id}/deliveries/{delivery.public_id}/"
    return workspace, client, subscription, delivery, url


def test_inspector_retains_exact_wire_attempts_across_replay_and_destination_change(monkeypatch):
    workspace, client, subscription, delivery, url = inspected_delivery()
    monkeypatch.setattr(socket, "getaddrinfo", public_dns)
    captured = []

    def send(sub, event, body, *, headers):
        attempt = delivery.history.latest("pk")
        assert attempt.completed_at is None
        assert attempt.body.encode() == body
        assert attempt.headers == headers
        assert attempt.destination == sub.url
        captured.append((body, headers))
        return 204

    with patch("integrations.webhooks.send_delivery", side_effect=send):
        assert deliver_pending() == 1
    detail = client.get(url).json()
    assert detail["next_body"].encode() == captured[0][0]
    assert detail["body_sha256"] == hashlib.sha256(captured[0][0]).hexdigest()
    attempt = detail["history"][0]
    expected = hmac.new(
        signing_secret(subscription).encode(),
        attempt["headers"]["X-Conflux-Timestamp"].encode() + b"." + attempt["body"].encode(),
        hashlib.sha256,
    ).hexdigest()
    assert attempt["headers"]["X-Conflux-Signature"] == "v1=" + expected
    assert "secret" not in detail
    assert attempt["status_code"] == 204 and attempt["completed_at"]
    assert (
        client.patch(
            base(workspace) + f"{subscription.public_id}/",
            {"url": "https://new.example/hook"},
            content_type="application/json",
        ).status_code
        == 200
    )
    assert client.post(url + "replay/").status_code == 200
    assert client.post(url + "replay/").status_code == 400
    with patch("integrations.webhooks.send_delivery", side_effect=send):
        assert deliver_pending() == 1
    detail = client.get(url).json()
    assert [row["destination"] for row in detail["history"]] == [
        "https://new.example/hook",
        "https://receiver.example/hook",
    ]
    assert detail["destination"] == "https://new.example/hook"
    assert detail["attempts"] == 1
    assert detail["history"][0]["headers"]["X-Conflux-Event-Id"] == detail["event_id"]
    assert detail["history"][1] == attempt


@pytest.mark.parametrize("role", [Role.PARTICIPANT, Role.JUDGE])
def test_inspector_and_destination_changes_require_organizer(role):
    workspace, _, subscription, delivery, url = inspected_delivery()
    user = User.objects.create_user(username="reader")
    Membership.objects.create(workspace=workspace, user=user, role=role)
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    assert client.get(url).status_code == 403
    assert client.post(url + "replay/").status_code == 403
    assert (
        client.patch(
            base(workspace) + f"{subscription.public_id}/",
            {"enabled": False},
            content_type="application/json",
        ).status_code
        == 403
    )
    assert Client().get(url).status_code in (401, 403)
    assert delivery.history.count() == 0


def test_inspector_scopes_ids_and_is_read_only():
    workspace, client, subscription, delivery, url = inspected_delivery()
    other = WebhookSubscription.objects.create(workspace=workspace, url="https://other.example/")
    assert (
        client.get(url.replace(str(subscription.public_id), str(other.public_id))).status_code
        == 404
    )
    other_workspace = Workspace.objects.create(name="Other", slug="other-inspection")
    organizer = User.objects.get(username="webhook-organizer")
    Membership.objects.create(workspace=other_workspace, user=organizer, role=Role.ORGANIZER)
    assert (
        client.get(
            url.replace(str(workspace.public_id), str(other_workspace.public_id))
        ).status_code
        == 404
    )
    with patch("integrations.webhooks.send_delivery") as sender:
        detail = client.get(url).json()
    sender.assert_not_called()
    assert detail["history"] == [] and not detail["history_has_more"]
    delivery.refresh_from_db()
    assert delivery.attempts == 0 and delivery.status == "pending"
    assert client.get(url + "?offset=-1").status_code == 400
    assert client.get(url + "?offset=no").status_code == 400


def test_invalid_destination_update_and_disabled_replay_fail_closed(monkeypatch):
    workspace, client, subscription, delivery, url = inspected_delivery()
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))],
    )
    assert (
        client.patch(
            base(workspace) + f"{subscription.public_id}/",
            {"url": "https://internal.example/", "enabled": False},
            content_type="application/json",
        ).status_code
        == 400
    )
    subscription.refresh_from_db()
    assert subscription.enabled and subscription.url == "https://receiver.example/hook"
    subscription.enabled = False
    subscription.save()
    delivery.status = "dead"
    delivery.save()
    assert client.post(url + "replay/").status_code == 400
    assert deliver_pending() == 0


def test_attempt_history_paginates_without_losing_prior_attempts():
    _, client, _, delivery, url = inspected_delivery()
    WebhookAttempt.objects.bulk_create(
        [
            WebhookAttempt(
                delivery=delivery, destination="https://receiver.example/", body=str(i), headers={}
            )
            for i in range(105)
        ]
    )
    first = client.get(url).json()
    second = client.get(url + "?offset=100").json()
    assert len(first["history"]) == 100 and first["history_has_more"]
    assert len(second["history"]) == 5 and not second["history_has_more"]
    ids = [row["public_id"] for row in first["history"] + second["history"]]
    assert len(set(ids)) == 105


def test_failed_attempt_and_stale_claim_outcomes_are_preserved():
    _, client, _, delivery, url = inspected_delivery()
    with patch("integrations.webhooks.send_delivery", side_effect=TimeoutError("Timed out")):
        assert deliver_pending() == 1
    detail = client.get(url).json()
    assert detail["history"][0]["error"] == "Timed out"
    assert detail["history"][0]["status_code"] is None
    assert detail["next_attempt_at"] and detail["status"] == "pending"
    WebhookDelivery.objects.filter(pk=delivery.pk).update(next_attempt_at=timezone.now())

    def stale_send(*args, **kwargs):
        WebhookDelivery.objects.filter(pk=delivery.pk).update(next_attempt_at=timezone.now())
        with patch("integrations.webhooks.send_delivery", return_value=204):
            assert deliver_pending() == 1
        return 503

    with patch("integrations.webhooks.send_delivery", side_effect=stale_send):
        deliver_pending()
    detail = client.get(url).json()
    assert detail["status"] == "succeeded" and detail["last_status_code"] == 204
    assert [row["status_code"] for row in detail["history"]] == [204, 503, None]


def test_inspector_rejects_bearer_only_credentials():
    workspace, client, subscription, _, url = inspected_delivery()
    issued = client.post(
        f"/api/v1/workspaces/{workspace.public_id}/api-credentials/",
        {"name": "Event reader", "allowed_actions": ["GET:event-list"]},
        content_type="application/json",
    )
    assert issued.status_code == 201
    bearer = Client(HTTP_AUTHORIZATION=f"Bearer {issued.json()['token']}")
    assert bearer.get(url).status_code == 401
    assert bearer.post(url + "replay/").status_code == 401
    assert (
        bearer.patch(
            base(workspace) + f"{subscription.public_id}/",
            {"enabled": False},
            content_type="application/json",
        ).status_code
        == 401
    )
