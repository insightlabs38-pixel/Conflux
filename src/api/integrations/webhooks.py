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

from .models import WebhookDelivery, WebhookSubscription

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


def send_delivery(subscription, domain_event, body):
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
            headers=signed_headers(subscription, domain_event, body),
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
        try:
            body = json.dumps(
                envelope(delivery.domain_event), separators=(",", ":"), sort_keys=True
            ).encode()
            status = send_delivery(delivery.subscription, delivery.domain_event, body)
            error = "" if 200 <= status < 300 else f"HTTP {status}"
        except (OSError, ValueError, TimeoutError, http.client.HTTPException) as exc:
            status = None
            error = str(exc)[:200]
        with transaction.atomic():
            delivery = WebhookDelivery.objects.select_for_update().get(pk=pk)
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
