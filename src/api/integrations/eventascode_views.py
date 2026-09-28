from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from events.views import OrganizerView
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from . import eventascode


class EventAsCodeDocumentInput(serializers.Serializer):
    document = serializers.JSONField()
    prune = serializers.BooleanField(default=False)

    def validate(self, attrs):
        if self.initial_data.keys() - self.fields.keys():
            raise ValidationError("Unknown fields.")
        return attrs


class EventAsCodeApplyInput(EventAsCodeDocumentInput):
    expected_digest = serializers.CharField(min_length=64, max_length=64)


class EventAsCodeView(OrganizerView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        return Response(
            {"digest": eventascode.digest(event), "document": eventascode.export_document(event)}
        )


class ValidateView(OrganizerView):
    @extend_schema(request=EventAsCodeDocumentInput, responses=OpenApiTypes.OBJECT)
    def post(self, request, workspace_public_id, event_public_id):
        data = EventAsCodeDocumentInput(data=request.data)
        data.is_valid(raise_exception=True)
        errors = eventascode.validate(self.get_event(), data.validated_data["document"])
        return Response({"valid": not errors, "errors": errors})


class PlanView(OrganizerView):
    @extend_schema(request=EventAsCodeDocumentInput, responses=OpenApiTypes.OBJECT)
    def post(self, request, workspace_public_id, event_public_id):
        data = EventAsCodeDocumentInput(data=request.data)
        data.is_valid(raise_exception=True)
        report = eventascode.plan(
            self.get_event(),
            data.validated_data["document"],
            prune=data.validated_data["prune"],
        )
        return Response({"ok": not report["errors"], **report})


class ApplyView(OrganizerView):
    @extend_schema(request=EventAsCodeApplyInput, responses=OpenApiTypes.OBJECT)
    def post(self, request, workspace_public_id, event_public_id):
        data = EventAsCodeApplyInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            report = eventascode.apply(
                self.get_event(),
                data.validated_data["document"],
                expected_digest=data.validated_data["expected_digest"],
                actor=request.user,
                prune=data.validated_data["prune"],
            )
        except eventascode.StaleDigest as exc:
            return Response({"detail": str(exc), "current_digest": exc.current}, status=409)
        if report["errors"]:
            return Response({"ok": False, **report}, status=400)
        return Response({"ok": True, **report})
