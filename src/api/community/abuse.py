"""Rate limiting and abuse signaling (ABUSE-001/002).

Deliberately DB-backed rather than a cache-based limiter: this project has
no cache backend configured (Valkey is reserved for Celery/broker state per
ARCHITECTURE.md, never authoritative), and a rate limit that silently stops
working if a cache is unavailable is worse than a slightly heavier table.
`RateLimitEvent` rows are cheap to prune and never carry raw identifiers.
"""

import hashlib
import ipaddress
from datetime import timedelta

from audit.services import record_mutation
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import AbuseSignal, AbuseSignalType, RateLimitEvent


def _hash(plan, scope: str, identifier: str) -> str:
    # Salted with SECRET_KEY so the hash can't be reversed by guessing +
    # hashing candidate emails/IPs offline.
    return hashlib.sha256(
        f"{settings.SECRET_KEY}:{plan.pk}:{scope}:{identifier}".encode()
    ).hexdigest()


def client_identifier(request) -> str:
    """A best-effort, privacy-respecting client identifier for rate limiting
    only -- never stored raw, never used for anything but counting.
    """
    remote = request.META.get("REMOTE_ADDR", "unknown")
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded and _internal(remote):
        # The bundled Caddy replaces any client-supplied X-Forwarded-For with the real
        # peer, so behind it the first entry is the visitor rather than the proxy that
        # every visitor would otherwise share a rate limit through.
        candidate = forwarded.split(",")[0].strip()
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            return remote
        return candidate
    return remote


def _internal(address):
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local


def enforce_rate_limit(plan, scope: str, identifier: str, *, limit: int, window: timedelta):
    """Raises ValidationError and records an AbuseSignal if `identifier` has
    made >= `limit` attempts in `scope` within `window`; otherwise records
    this attempt and returns normally.
    """
    key_hash = _hash(plan, scope, identifier)
    # Serialize checks for this plan. A count followed by an insert without a
    # row lock lets concurrent requests exceed the limit on PostgreSQL.
    with transaction.atomic():
        type(plan).objects.select_for_update().get(pk=plan.pk)
        cutoff = timezone.now() - window
        count = RateLimitEvent.objects.filter(
            scope=scope, key_hash=key_hash, created_at__gte=cutoff
        ).count()
        if count < limit:
            RateLimitEvent.objects.create(scope=scope, key_hash=key_hash)
            return
    record_signal(
        plan,
        AbuseSignalType.RATE_LIMIT_EXCEEDED,
        f"{scope}: {count + 1} attempts within {window}, limit is {limit}.",
        {
            "scope": scope,
            "count": count + 1,
            "limit": limit,
            "window_seconds": window.total_seconds(),
        },
    )
    raise ValidationError("Too many attempts. Please try again later.")


def record_signal(plan, signal_type: str, detail: str, evidence: dict | None = None):
    with transaction.atomic():
        signal = AbuseSignal.objects.create(
            plan=plan, signal_type=signal_type, detail=detail, evidence=evidence or {}
        )
        record_mutation(
            actor=None,
            workspace=plan.event.workspace,
            action="community_abuse.detected",
            target=signal,
            metadata={"event_id": str(plan.event.public_id), "signal_type": signal_type},
        )
    return signal
