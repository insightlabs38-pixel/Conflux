from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError
from drf_spectacular.utils import extend_schema
from events.views import OrganizerView
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .bulk import StalePreview, run_bulk
from .bulk_schema import BulkRequest, BulkResponse


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
        except (ModelValidationError, ValueError, IntegrityError, OverflowError) as exc:
            detail = (
                exc.messages
                if isinstance(exc, ModelValidationError)
                else ["Bulk operation is invalid."]
            )
            raise ValidationError({"detail": detail}) from exc
        return Response(result)
