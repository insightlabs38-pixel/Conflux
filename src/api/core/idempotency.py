import hashlib
import json

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone

from .models import IdempotencyKey

IDEMPOTENCY_HEADER = "HTTP_IDEMPOTENCY_KEY"


class IdempotentMixin:
    """Dedupe unsafe requests by a client-supplied `Idempotency-Key` header.

    Put before the DRF view class in the MRO. Requests without the header are
    passed through untouched, so normal (non-idempotent) callers see no change.
    A replayed key with a different body is rejected rather than silently
    served the stale response.
    """

    idempotent_methods = ("POST", "PUT", "PATCH")

    def dispatch(self, request, *args, **kwargs):
        key = request.META.get(IDEMPOTENCY_HEADER)
        if not key or request.method not in self.idempotent_methods:
            return super().dispatch(request, *args, **kwargs)

        body_hash = hashlib.sha256(request.body or b"").hexdigest()
        with transaction.atomic():
            record, created = IdempotencyKey.objects.get_or_create(
                key=key,
                defaults={
                    "method": request.method,
                    "path": request.path,
                    "request_hash": body_hash,
                },
            )

        if not created:
            if record.request_hash != body_hash:
                return JsonResponse(
                    {"detail": "Idempotency key reused with a different request body."},
                    status=422,
                )
            if record.response_status is not None:
                return JsonResponse(
                    record.response_body or {}, status=record.response_status, safe=False
                )

        response = super().dispatch(request, *args, **kwargs)
        if hasattr(response, "render"):
            response.render()
        try:
            body = json.loads(response.content) if response.content else None
        except ValueError:
            body = None
        record.response_status = response.status_code
        record.response_body = body
        record.completed_at = timezone.now()
        record.save(update_fields=["response_status", "response_body", "completed_at"])
        return response
