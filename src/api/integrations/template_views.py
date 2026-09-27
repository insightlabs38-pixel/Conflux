from accounts.authentication import CookieSessionAuthentication
from audit.services import record_mutation
from core.mixins import WorkspaceLookupMixin
from core.permissions import require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from events.models import Event
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role

from .archive_views import ImportedEventOutput
from .models import EventTemplate
from .template_library import instantiate_library_template, list_library
from .templates import clone_event, instantiate_template, save_template


class EventTemplateOutput(serializers.Serializer):
    public_id = serializers.UUIDField()
    name = serializers.CharField()
    source_event_name = serializers.CharField()
    sections = serializers.ListField(child=serializers.CharField())
    created_at = serializers.DateTimeField()


class EventTemplateCreateInput(serializers.Serializer):
    event = serializers.UUIDField()
    name = serializers.CharField(max_length=160)
    sections = serializers.ListField(child=serializers.CharField(), required=False)


class LibraryTemplateOutput(serializers.Serializer):
    slug = serializers.SlugField()
    label = serializers.CharField()
    description = serializers.CharField()
    tracks = serializers.ListField(child=serializers.CharField())
    stages = serializers.ListField(child=serializers.CharField())


class InstantiateInput(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    slug = serializers.SlugField(max_length=200)


class CloneInput(InstantiateInput):
    sections = serializers.ListField(child=serializers.CharField(), required=False)


def _template_data(template):
    return {
        "public_id": str(template.public_id),
        "name": template.name,
        "source_event_name": template.source_event_name,
        "sections": template.sections,
        "created_at": template.created_at,
    }


class _WorkspaceRoleView(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]


class EventTemplateListView(_WorkspaceRoleView):
    @extend_schema(responses=EventTemplateOutput(many=True))
    def get(self, request, workspace_public_id):
        templates = EventTemplate.objects.filter(workspace=self.get_workspace())
        return Response([_template_data(item) for item in templates])

    @extend_schema(request=EventTemplateCreateInput, responses={201: EventTemplateOutput})
    def post(self, request, workspace_public_id):
        data = EventTemplateCreateInput(data=request.data)
        data.is_valid(raise_exception=True)
        workspace = self.get_workspace()
        source_event = get_object_or_404(
            Event, workspace=workspace, public_id=data.validated_data["event"]
        )
        try:
            with transaction.atomic():
                template = save_template(
                    event=source_event,
                    name=data.validated_data["name"],
                    actor=request.user,
                    sections=data.validated_data.get("sections"),
                )
                record_mutation(
                    actor=request.user,
                    workspace=workspace,
                    action="event_template.saved",
                    target=template,
                    event_type="event_template.saved",
                    payload={
                        "event": str(source_event.public_id),
                        "template": str(template.public_id),
                    },
                )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(_template_data(template), status=201)


class TemplateLibraryListView(_WorkspaceRoleView):
    @extend_schema(responses=LibraryTemplateOutput(many=True))
    def get(self, request, workspace_public_id):
        return Response(list_library())


class TemplateLibraryInstantiateView(_WorkspaceRoleView):
    @extend_schema(request=InstantiateInput, responses={201: ImportedEventOutput})
    def post(self, request, workspace_public_id, template_slug):
        data = InstantiateInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                event = instantiate_library_template(
                    workspace=self.get_workspace(),
                    template_slug=template_slug,
                    name=data.validated_data["name"],
                    slug=data.validated_data["slug"],
                )
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="event_template.library_instantiated",
                    target=event,
                    event_type="event_template.library_instantiated",
                    payload={"template": template_slug, "event": str(event.public_id)},
                )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(
            {"public_id": event.public_id, "name": event.name, "slug": event.slug}, status=201
        )


class EventTemplateDetailView(_WorkspaceRoleView):
    @extend_schema(request=None, responses={204: None})
    def delete(self, request, workspace_public_id, template_public_id):
        template = get_object_or_404(
            EventTemplate, workspace=self.get_workspace(), public_id=template_public_id
        )
        with transaction.atomic():
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="event_template.deleted",
                target=template,
                metadata={"name": template.name},
            )
            template.delete()
        return Response(status=204)


class EventTemplateInstantiateView(_WorkspaceRoleView):
    @extend_schema(request=InstantiateInput, responses={201: ImportedEventOutput})
    def post(self, request, workspace_public_id, template_public_id):
        data = InstantiateInput(data=request.data)
        data.is_valid(raise_exception=True)
        workspace = self.get_workspace()
        template = get_object_or_404(
            EventTemplate, workspace=workspace, public_id=template_public_id
        )
        try:
            with transaction.atomic():
                event = instantiate_template(
                    template=template,
                    workspace=workspace,
                    name=data.validated_data["name"],
                    slug=data.validated_data["slug"],
                )
                record_mutation(
                    actor=request.user,
                    workspace=workspace,
                    action="event_template.instantiated",
                    target=event,
                    event_type="event_template.instantiated",
                    payload={"template": str(template.public_id), "event": str(event.public_id)},
                )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(
            {"public_id": event.public_id, "name": event.name, "slug": event.slug}, status=201
        )


class EventCloneView(_WorkspaceRoleView):
    def get_event(self):
        return get_object_or_404(
            Event, workspace=self.get_workspace(), public_id=self.kwargs["event_public_id"]
        )

    @extend_schema(request=CloneInput, responses={201: ImportedEventOutput})
    def post(self, request, workspace_public_id, event_public_id):
        data = CloneInput(data=request.data)
        data.is_valid(raise_exception=True)
        source_event = self.get_event()
        try:
            with transaction.atomic():
                cloned = clone_event(
                    event=source_event,
                    name=data.validated_data["name"],
                    slug=data.validated_data["slug"],
                    sections=data.validated_data.get("sections"),
                )
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="event.cloned",
                    target=cloned,
                    event_type="event.cloned",
                    payload={
                        "source_event": str(source_event.public_id),
                        "event": str(cloned.public_id),
                    },
                )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(
            {"public_id": cloned.public_id, "name": cloned.name, "slug": cloned.slug}, status=201
        )
