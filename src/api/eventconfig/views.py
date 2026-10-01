from audit.services import record_mutation
from core import explain
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from drf_spectacular.utils import OpenApiParameter, extend_schema
from events.models import Event
from events.views import OrganizerView
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from . import modules
from .configuration import FILTER_CHOICES, effective_configuration
from .consequences import ACTIONS, STATUS_ACTIONS, preview, target_for
from .generated import generated_configuration
from .readiness import compute_readiness
from .schema import (
    ConfigurationSchema,
    ConsequencesSchema,
    GeneratedConfigurationSchema,
    ReadinessSchema,
    WorkflowSchema,
)
from .workflow import workflow_state


class ModuleHomeSchema(serializers.Serializer):
    destination = serializers.CharField()
    section = serializers.CharField(allow_blank=True)


class ModuleSchema(serializers.Serializer):
    key = serializers.SlugField()
    label = serializers.CharField()
    description = serializers.CharField()
    destination = serializers.CharField(allow_null=True)
    home = ModuleHomeSchema()
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


class EventReadinessView(OrganizerView):
    """What is missing before this event can launch: the canonical readiness list."""

    @extend_schema(responses=ReadinessSchema)
    def get(self, request, workspace_public_id, event_public_id):
        return Response(compute_readiness(self.get_event()))


class EventConfigurationView(OrganizerView):
    """Every setting of the event with value, default, baseline, source and lock, so automation
    never has to reverse-engineer what the UI shows."""

    @extend_schema(
        parameters=[
            OpenApiParameter("module", str, description="Only this module (core, onsite, ...)."),
            OpenApiParameter("tier", str, enum=list(FILTER_CHOICES["tier"])),
            OpenApiParameter("source", str, enum=list(FILTER_CHOICES["source"])),
            OpenApiParameter("key", str, description="Key prefix, e.g. registration."),
        ],
        responses=ConfigurationSchema,
    )
    def get(self, request, workspace_public_id, event_public_id):
        filters = {
            name: request.query_params.get(name) or None
            for name in ("module", "tier", "source", "key")
        }
        for name, allowed in FILTER_CHOICES.items():
            if filters[name] and filters[name] not in allowed:
                raise ValidationError({name: f"Unknown {name}; use one of {', '.join(allowed)}."})
        return Response(effective_configuration(self.get_event(), **filters))


class EventWorkflowView(OrganizerView):
    """Whether the event still follows its format's workflow, and what changed if not."""

    @extend_schema(responses=WorkflowSchema)
    def get(self, request, workspace_public_id, event_public_id):
        return Response(workflow_state(self.get_event()))


class EventGeneratedConfigurationView(OrganizerView):
    """The event's configuration stating only what is necessary: what the organizer set or changed
    from the format, with everything inherited listed beside it for reading."""

    @extend_schema(responses=GeneratedConfigurationSchema)
    def get(self, request, workspace_public_id, event_public_id):
        return Response(generated_configuration(self.get_event()))


class EventConsequencesView(OrganizerView):
    """What a destructive or high-impact operation would do, before it is done. Read-only: the
    operation's own endpoint still validates, authorizes and audits."""

    @extend_schema(
        parameters=[
            OpenApiParameter("action", str, enum=list(ACTIONS), required=True),
            OpenApiParameter("target", str, description="Id of the stage, link, track or prize."),
        ],
        responses=ConsequencesSchema,
    )
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        action = request.query_params.get("action")
        if action not in ACTIONS:
            raise ValidationError({"action": f"Unknown action; use one of {', '.join(ACTIONS)}."})
        target = None
        if action not in STATUS_ACTIONS and action != "event.delete":
            public_id = request.query_params.get("target")
            try:
                target = target_for(action, event, public_id) if public_id else None
            except (ValueError, TypeError, ModelValidationError):
                target = None
            if target is None:
                raise ValidationError({"target": "Name the existing item the action applies to."})
        shown = preview(action, event, target)
        return Response({**shown, "explanation": explain.from_consequences(shown)})
