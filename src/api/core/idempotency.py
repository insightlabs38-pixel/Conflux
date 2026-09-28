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


def _scope(request):
    """Who is asking: keys never cross callers, so one caller can neither read
    nor block another's cached response.
    """
    credentials = (
        request.COOKIES.get("session", "") + "|" + request.META.get("HTTP_AUTHORIZATION", "")
    )
    return hashlib.sha256(credentials.encode()).hexdigest()


class IdempotentMixin:
    """Dedupe unsafe requests by a client-supplied `Idempotency-Key` header.

    Put before the DRF view class in the MRO. Requests without the header are
    passed through untouched. A key is private to the caller and to one
    method+path; reusing it for a different request is rejected (422), a
    duplicate while the first is still running is refused (409) instead of
    running twice, and server errors are never cached so they can be retried.
    """

    idempotent_methods = ("POST", "PUT", "PATCH")

    def dispatch(self, request, *args, **kwargs):
        key = request.META.get(IDEMPOTENCY_HEADER)
        if not key or request.method not in self.idempotent_methods:
            return super().dispatch(request, *args, **kwargs)
        if len(key) > MAX_KEY_LENGTH:
            return JsonResponse({"detail": "Idempotency key is too long."}, status=400)

        fingerprint = hashlib.sha256(
            request.method.encode() + b"\n" + request.path.encode() + b"\n" + (request.body or b"")
        ).hexdigest()
        scoped = f"{_scope(request)}:{key}"
        with transaction.atomic():
            record, created = IdempotencyKey.objects.select_for_update().get_or_create(
                key=scoped,
                defaults={
                    "method": request.method,
                    "path": request.path,
                    "request_hash": fingerprint,
                },
            )
            if not created:
                if record.request_hash != fingerprint:
                    return JsonResponse(
                        {"detail": "Idempotency key reused with a different request."}, status=422
                    )
                if record.response_status is not None:
                    return JsonResponse(
                        record.response_body or {}, status=record.response_status, safe=False
                    )
                if timezone.now() - record.created_at < IN_FLIGHT_TIMEOUT:
                    return JsonResponse(
                        {"detail": "A request with this key is still being processed."},
                        status=409,
                    )
                record.created_at = timezone.now()
                record.save(update_fields=["created_at"])

        try:
            response = super().dispatch(request, *args, **kwargs)
            if hasattr(response, "render"):
                response.render()
        except BaseException:
            IdempotencyKey.objects.filter(pk=record.pk).delete()
            raise
        if response.status_code >= 500:
            IdempotencyKey.objects.filter(pk=record.pk).delete()
            return response
        try:
            body = json.loads(response.content) if response.content else None
        except ValueError:
            body = None
        record.response_status = response.status_code
        record.response_body = body
        record.completed_at = timezone.now()
        record.save(update_fields=["response_status", "response_body", "completed_at"])
        return response
