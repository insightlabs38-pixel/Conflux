import hashlib
import hmac
import http.client
import ipaddress
import json
import socket
from datetime import timedelta
from urllib.parse import urlsplit

from audit.models import DomainEvent
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from .models import WebhookAttempt, WebhookDelivery, WebhookPlatform, WebhookSubscription

ENVELOPE_VERSION = "1"
MAX_ATTEMPTS = 5


def validate_destination(url):
    try:
        parts = urlsplit(url)
        host = parts.hostname
        port = parts.port
    except ValueError as exc:
        raise ValueError("Invalid webhook URL.") from exc
    if (
        parts.scheme != "https"
        or not host
        or port not in (None, 443)
        or parts.username is not None
        or parts.password is not None
        or parts.fragment
        or not parts.netloc
        or len(url) > 2048
    ):
        raise ValueError("Webhook URL must be a public HTTPS address on port 443.")
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("Webhook host could not be resolved.") from exc
    if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
        raise ValueError("Webhook host must resolve only to public addresses.")
    return parts, addresses[0][4][0]


def signing_secret(subscription):
    message = f"conflux-webhook-v1:{subscription.public_id}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()


def envelope(domain_event):
    return {
        "version": ENVELOPE_VERSION,
        "id": str(domain_event.public_id),
        "type": domain_event.event_type,
        "created_at": domain_event.created_at.isoformat(),
        "workspace": str(domain_event.workspace.public_id),
        "data": domain_event.payload,
    }


def chat_summary(domain_event) -> str:
    """A short, human-readable line for a chat platform (S23). Only
    scalar payload fields are rendered -- nested structures and internal
    IDs stay in the full `envelope()` a generic subscription still gets,
    never dumped raw into a chat message.
    """
    label = domain_event.event_type.replace(".", " ").replace("_", " ")
    details = ", ".join(
        f"{key}: {value}"
        for key, value in domain_event.payload.items()
        if key != "event" and isinstance(value, (str, int, float, bool))
    )
    return f"Conflux — {label}" + (f" ({details})" if details else "")


def payload_for(subscription, domain_event):
    """The JSON body a delivery should send: the signed envelope for a
    generic subscription, or a platform-native chat message otherwise.
    """
    if subscription.platform == WebhookPlatform.DISCORD:
        return {"content": chat_summary(domain_event)}
    if subscription.platform == WebhookPlatform.SLACK:
        return {"text": chat_summary(domain_event)}
    return envelope(domain_event)


def signed_headers(subscription, domain_event, body, now=None):
    timestamp = str(int((now or timezone.now()).timestamp()))
    signature = hmac.new(
        signing_secret(subscription).encode(), timestamp.encode() + b"." + body, hashlib.sha256
    ).hexdigest()
    return {
        "Content-Type": "application/json",
        "X-Conflux-Event-Id": str(domain_event.public_id),
        "X-Conflux-Timestamp": timestamp,
        "X-Conflux-Signature": f"v1={signature}",
    }


def delivery_body(subscription, domain_event):
    return json.dumps(
        payload_for(subscription, domain_event), separators=(",", ":"), sort_keys=True
    ).encode()


def send_delivery(subscription, domain_event, body, *, headers=None):
    parts, address = validate_destination(subscription.url)
    host = parts.hostname
    connection = http.client.HTTPSConnection(host, 443, timeout=5)
    connection._create_connection = (
        lambda _address, timeout, source_address: socket.create_connection(
            (address, 443), timeout, source_address
        )
    )
    try:
        connection.request(
            "POST",
            (parts.path or "/") + ("?" + parts.query if parts.query else ""),
            body=body,
            headers=headers
            if headers is not None
            else signed_headers(subscription, domain_event, body),
        )
        response = connection.getresponse()
        response.read(4096)
        return response.status
    finally:
        connection.close()


def stage_deliveries(limit=100):
    staged = 0
    with transaction.atomic():
        events = (
            DomainEvent.objects.select_for_update(skip_locked=True, of=("self",))
            .filter(status=DomainEvent.Status.PENDING, workspace__isnull=False)
            .select_related("workspace")
            .order_by("created_at")[:limit]
        )
        for event in events:
            subscriptions = WebhookSubscription.objects.filter(
                workspace=event.workspace, enabled=True
            ).select_related("event")
            for subscription in subscriptions:
                if event.event_type not in subscription.event_types:
                    continue
                if subscription.event_id and str(subscription.event.public_id) != str(
                    event.payload.get("event")
                ):
                    continue
                _, created = WebhookDelivery.objects.get_or_create(
                    subscription=subscription, domain_event=event
                )
                staged += int(created)
            event.status = DomainEvent.Status.PROCESSED
            event.processed_at = timezone.now()
            event.save(update_fields=["status", "processed_at"])
    return staged


def deliver_pending(limit=100):
    delivered = 0
    now = timezone.now()
    ids = list(
        WebhookDelivery.objects.filter(status=WebhookDelivery.Status.PENDING)
        .filter(models.Q(next_attempt_at__isnull=True) | models.Q(next_attempt_at__lte=now))
        .order_by("created_at")
        .values_list("pk", flat=True)[:limit]
    )
    for pk in ids:
        with transaction.atomic():
            delivery = (
                WebhookDelivery.objects.select_for_update(of=("self",))
                .select_related("subscription", "domain_event", "domain_event__workspace")
                .get(pk=pk)
            )
            if delivery.status != WebhookDelivery.Status.PENDING or (
                delivery.next_attempt_at and delivery.next_attempt_at > timezone.now()
            ):
                continue
            if not delivery.subscription.enabled:
                continue
            # Commit the claim before any network I/O. A worker crash may cause
            # a duplicate delivery, so receivers must dedupe on event ID.
            delivery.attempts += 1
            delivery.next_attempt_at = timezone.now() + timedelta(minutes=10)
            delivery.save(update_fields=["attempts", "next_attempt_at"])
            body = delivery_body(delivery.subscription, delivery.domain_event)
            headers = signed_headers(delivery.subscription, delivery.domain_event, body)
            attempt = WebhookAttempt.objects.create(
                delivery=delivery,
                destination=delivery.subscription.url,
                body=body.decode(),
                headers=headers,
            )
        try:
            status = send_delivery(
                delivery.subscription, delivery.domain_event, body, headers=headers
            )
            error = "" if 200 <= status < 300 else f"HTTP {status}"
        except (OSError, ValueError, TimeoutError, http.client.HTTPException) as exc:
            status = None
            error = str(exc)[:200]
        with transaction.atomic():
            delivery = WebhookDelivery.objects.select_for_update().get(pk=pk)
            attempt.status_code = status
            attempt.error = error
            attempt.completed_at = timezone.now()
            attempt.save(update_fields=["status_code", "error", "completed_at"])
            # An expired claim can finish after a newer attempt has taken over.
            if delivery.history.filter(pk__gt=attempt.pk).exists():
                continue
            delivery.last_status_code = status
            delivery.last_error = error
            if not error:
                delivery.status = WebhookDelivery.Status.SUCCEEDED
                delivery.completed_at = timezone.now()
                delivery.next_attempt_at = None
            elif delivery.attempts >= MAX_ATTEMPTS:
                delivery.status = WebhookDelivery.Status.DEAD
                delivery.completed_at = timezone.now()
                delivery.next_attempt_at = None
            else:
                delivery.next_attempt_at = timezone.now() + timedelta(
                    minutes=min(60, 2**delivery.attempts)
                )
            delivery.save()
            delivered += 1
    return delivered
