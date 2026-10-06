import hashlib
import json
from datetime import timedelta

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone

from .models import IdempotencyKey

IDEMPOTENCY_HEADER = "HTTP_IDEMPOTENCY_KEY"
MAX_KEY_LENGTH = 190
IN_FLIGHT_TIMEOUT = timedelta(minutes=2)
KEY_TTL = timedelta(hours=24)


class _Early(Exception):
    """A response decided before the view runs (a replay, a refusal of the key)."""

    def __init__(self, response):
        super().__init__()
        self.response = response


def purge(now=None) -> int:
    """Forget keys older than KEY_TTL: the stored response is a copy of what the caller was
    sent, so it is kept for retries and no longer."""
    now = now or timezone.now()
    return IdempotencyKey.objects.filter(created_at__lt=now - KEY_TTL).delete()[0]


class IdempotentMixin:
    """Dedupe unsafe requests by a client-supplied `Idempotency-Key` header.

    Put before the DRF view class in the MRO. Requests without the header, and requests by a
    caller who is not signed in, are passed through untouched. The key is considered only after
    DRF has authenticated the caller and checked the view's permissions, so a replay is never
    served to someone the view would refuse. A key is private to the signed-in user and to one
    method+path; reusing it for a different request is rejected (422), a duplicate while the
    first is still running is refused (409) instead of running twice, and server errors are never
    cached so they can be retried. A refusal (4xx) is remembered like any answer: fix the request
    and send a new key. Keys are forgotten after a day (`purge`).
    """

    idempotent_methods = ("POST", "PUT", "PATCH")

    def initial(self, request, *args, **kwargs):
        self._idempotency = None
        super().initial(request, *args, **kwargs)  # authentication, permissions, throttles
        key = request.META.get(IDEMPOTENCY_HEADER)
        user = getattr(request, "user", None)
        if not key or request.method not in self.idempotent_methods:
            return
        if user is None or not user.is_authenticated:
            return
        if len(key) > MAX_KEY_LENGTH:
            raise _Early(JsonResponse({"detail": "Idempotency key is too long."}, status=400))
        body = request._request.body if hasattr(request, "_request") else request.body
        fingerprint = hashlib.sha256(
            request.method.encode() + b"\n" + request.path.encode() + b"\n" + (body or b"")
        ).hexdigest()
        scoped = f"user:{user.pk}:{key}"
        with transaction.atomic():
            record, created = IdempotencyKey.objects.select_for_update().get_or_create(
                key=scoped,
                defaults={
                    "method": request.method,
                    "path": request.path,
                    "request_hash": fingerprint,
                },
            )
            if not created and record.created_at < timezone.now() - KEY_TTL:
                record.delete()  # expired: this is a new request under a reused key
                record = IdempotencyKey.objects.create(
                    key=scoped,
                    method=request.method,
                    path=request.path,
                    request_hash=fingerprint,
                )
                created = True
            if not created:
                if record.request_hash != fingerprint:
                    raise _Early(
                        JsonResponse(
                            {"detail": "Idempotency key reused with a different request."},
                            status=422,
                        )
                    )
                if record.response_status is not None:
                    raise _Early(
                        JsonResponse(
                            record.response_body or {},
                            status=record.response_status,
                            safe=False,
                        )
                    )
                if timezone.now() - record.created_at < IN_FLIGHT_TIMEOUT:
                    raise _Early(
                        JsonResponse(
                            {"detail": "A request with this key is still being processed."},
                            status=409,
                        )
                    )
                record.created_at = timezone.now()
                record.save(update_fields=["created_at"])
        self._idempotency = record

    def handle_exception(self, exc):
        if isinstance(exc, _Early):
            return exc.response
        try:
            return super().handle_exception(exc)
        except BaseException:
            self._forget()
            raise

    def _forget(self):
        record, self._idempotency = getattr(self, "_idempotency", None), None
        if record is not None:
            IdempotencyKey.objects.filter(pk=record.pk).delete()

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        record = getattr(self, "_idempotency", None)
        if record is None:
            return response
        if response.status_code >= 500:
            self._forget()
            return response
        if hasattr(response, "render") and not getattr(response, "is_rendered", True):
            response.render()
        try:
            body = json.loads(response.content) if response.content else None
        except ValueError:
            body = None
        record.response_status = response.status_code
        record.response_body = body
        record.completed_at = timezone.now()
        record.save(update_fields=["response_status", "response_body", "completed_at"])
        self._idempotency = None
        return response
