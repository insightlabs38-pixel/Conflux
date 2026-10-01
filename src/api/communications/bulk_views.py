from core.approvals import ApprovalRequired
from core.pagination import page_params, paged_response
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from events.views import OrganizerView
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .bulk import StalePreview, run_bulk
from .bulk_schema import BulkReceiptSchema, BulkRequest, BulkResponse
from .models import BulkReceipt


class BulkOperationsView(OrganizerView):
    @extend_schema(request=BulkRequest, responses={200: BulkResponse})
    def post(self, request, workspace_public_id, event_public_id):
        serializer = BulkRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = run_bulk(
                event=self.get_event(), actor=request.user, **serializer.validated_data
            )
        except StalePreview as exc:
            return Response({"detail": str(exc)}, status=409)
        except ApprovalRequired as needed:
            return needed.respond(request.user)
        except (ModelValidationError, ValueError, IntegrityError, OverflowError) as exc:
            detail = (
                exc.messages
                if isinstance(exc, ModelValidationError)
                else ["Bulk operation is invalid."]
            )
            raise ValidationError({"detail": detail}) from exc
        return Response(result)


def _receipt(receipt, *, with_effects):
    effects = receipt.result.get("effects", [])
    body = {
        "public_id": str(receipt.public_id),
        "actor": receipt.actor.username,
        "created_at": receipt.created_at.isoformat().replace("+00:00", "Z"),
        "actions": [effect.get("action", "") for effect in effects],
    }
    if with_effects:
        body["effects"] = effects
    return body


class BulkReceiptListView(OrganizerView):
    """What was applied through the planner in this event, newest first (summaries)."""

    @extend_schema(
        parameters=[OpenApiParameter("limit", int), OpenApiParameter("offset", int)],
        responses=BulkReceiptSchema(many=True),
    )
    def get(self, request, workspace_public_id, event_public_id):
        limit, offset = page_params(request, default=25, maximum=100)
        receipts = BulkReceipt.objects.filter(event=self.get_event()).select_related("actor")
        return paged_response(
            request,
            receipts.order_by("-created_at", "-id"),
            lambda page: [_receipt(r, with_effects=False) for r in page],
            limit=limit,
            offset=offset,
        )


class BulkReceiptDetailView(OrganizerView):
    @extend_schema(responses=BulkReceiptSchema)
    def get(self, request, workspace_public_id, event_public_id, receipt_public_id):
        receipt = get_object_or_404(
            BulkReceipt.objects.select_related("actor"),
            event=self.get_event(),
            public_id=receipt_public_id,
        )
        return Response(_receipt(receipt, with_effects=True))
