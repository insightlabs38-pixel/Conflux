from audit.services import record_mutation
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from drf_spectacular.utils import OpenApiParameter, extend_schema
from events.models import Event
from events.views import OrganizerView
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from . import modules


class ModuleSchema(serializers.Serializer):
    key = serializers.SlugField()
    label = serializers.CharField()
    description = serializers.CharField()
    destination = serializers.CharField(allow_null=True)
    enabled = serializers.BooleanField()
    in_use = serializers.BooleanField()
    explicit = serializers.BooleanField(allow_null=True)
    can_disable = serializers.BooleanField()
    reason = serializers.CharField(allow_blank=True)


class ModuleListSchema(serializers.Serializer):
    scope = serializers.ChoiceField(choices=["event", "workspace"])
    event = serializers.UUIDField(allow_null=True)
    modules = ModuleSchema(many=True)


class ModuleInput(serializers.Serializer):
    enabled = serializers.BooleanField()


class WorkspaceModulesView(OrganizerView):
    """Optional modules for navigation: one event's effective state, or the workspace union."""

    @extend_schema(
        parameters=[
            OpenApiParameter("event", str, description="Event public id; omit for the union.")
        ],
        responses=ModuleListSchema,
    )
    def get(self, request, workspace_public_id):
        workspace = self.get_workspace()
        event = None
        requested = request.query_params.get("event")
        if requested:
            try:
                event = Event.objects.filter(workspace=workspace, public_id=requested).first()
            except (ValueError, ModelValidationError):
                event = None  # malformed id: same as an unknown one, the union applies
        if event is None:
            return Response(
                {
                    "scope": "workspace",
                    "event": None,
                    "modules": modules.workspace_modules(workspace),
                }
            )
        return Response(
            {
                "scope": "event",
                "event": str(event.public_id),
                "modules": modules.event_modules(event),
            }
        )


class EventModuleView(OrganizerView):
    @extend_schema(request=ModuleInput, responses=ModuleListSchema)
    def patch(self, request, workspace_public_id, event_public_id, module_key):
        data = ModuleInput(data=request.data)
        data.is_valid(raise_exception=True)
        event = self.get_event()
        self.ensure_mutable(event)
        enabled = data.validated_data["enabled"]
        try:
            with transaction.atomic():
                modules.set_enabled(event, module_key, enabled, actor=request.user)
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="event.module_enabled" if enabled else "event.module_disabled",
                    target=event,
                    metadata={"event_id": str(event.public_id), "module": module_key},
                )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(
            {
                "scope": "event",
                "event": str(event.public_id),
                "modules": modules.event_modules(event),
            }
        )
