from accounts.authentication import CookieSessionAuthentication
from core.mixins import WorkspaceLookupMixin
from core.permissions import require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from events.models import Event
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from stages.models import Stage
from workspaces.models import Role

from .external_qualifiers import import_external_qualifiers
from .models import ExternalQualifierImport

_PAGE_SIZE = 100


class QualifierEntryInput(serializers.Serializer):
    external_ref = serializers.CharField(max_length=120)
    project = serializers.UUIDField(required=False, allow_null=True)


class QualifierImportInput(serializers.Serializer):
    entries = QualifierEntryInput(many=True)


class QualifierEntryOutput(serializers.Serializer):
    external_ref = serializers.CharField()
    project = serializers.UUIDField()
    advanced = serializers.BooleanField()


class QualifierImportOutput(serializers.Serializer):
    public_id = serializers.UUIDField()
    stage = serializers.UUIDField()
    entries = QualifierEntryOutput(many=True)
    advanced_count = serializers.IntegerField()
    created_at = serializers.DateTimeField()


def _receipt_data(receipt):
    return {
        "public_id": str(receipt.public_id),
        "stage": str(receipt.stage.public_id),
        "entries": receipt.entries,
        "advanced_count": receipt.advanced_count,
        "created_at": receipt.created_at,
    }


class ExternalQualifierImportView(WorkspaceLookupMixin, APIView):
    """Reachable by an organizer's session or a scoped API credential
    (`CookieSessionAuthentication` supports both) -- the "API/webhook"
    surface for EXTQ-001.
    """

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    def get_stage(self):
        return get_object_or_404(
            Stage,
            event__workspace=self.get_workspace(),
            event__public_id=self.kwargs["event_public_id"],
            public_id=self.kwargs["stage_public_id"],
        )

    @extend_schema(responses=QualifierImportOutput(many=True))
    def get(self, request, workspace_public_id, event_public_id, stage_public_id):
        stage = self.get_stage()
        offset = _offset(request)
        receipts = ExternalQualifierImport.objects.filter(stage=stage).select_related("stage")[
            offset : offset + _PAGE_SIZE
        ]
        return Response([_receipt_data(item) for item in receipts])

    @extend_schema(request=QualifierImportInput, responses={201: QualifierImportOutput})
    def post(self, request, workspace_public_id, event_public_id, stage_public_id):
        data = QualifierImportInput(data=request.data)
        data.is_valid(raise_exception=True)
        stage = self.get_stage()
        event = get_object_or_404(Event, workspace=self.get_workspace(), public_id=event_public_id)
        try:
            receipt = import_external_qualifiers(
                event=event,
                stage=stage,
                entries=data.validated_data["entries"],
                actor=request.user,
            )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(_receipt_data(receipt), status=201)


def _offset(request):
    try:
        return max(int(request.query_params.get("offset", 0)), 0)
    except ValueError:
        return 0
