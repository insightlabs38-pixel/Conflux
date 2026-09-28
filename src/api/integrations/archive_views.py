from accounts.authentication import CookieSessionAuthentication
from audit.services import record_mutation
from core.mixins import WorkspaceLookupMixin
from core.permissions import require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from events.models import Event
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role

from .archive import build_archive, import_archive
from .migration_preview import preview_archive_import
from .signed_archive import sign_archive, verify_signed_archive


class ArchiveOutput(serializers.Serializer):
    format_version = serializers.IntegerField()
    mode = serializers.CharField()
    event = serializers.DictField()
    tracks = serializers.ListField(child=serializers.DictField())
    base_prizes = serializers.ListField(child=serializers.DictField())
    stages = serializers.ListField(child=serializers.DictField())
    stage_transitions = serializers.ListField(child=serializers.DictField())
    forms = serializers.ListField(child=serializers.DictField())
    policies = serializers.ListField(child=serializers.DictField())
    temporal_gates = serializers.ListField(child=serializers.DictField())
    policy_bindings = serializers.ListField(child=serializers.DictField())
    awards = serializers.ListField(child=serializers.DictField())
    projects = serializers.ListField(child=serializers.DictField(), required=False)


class ArchiveImportInput(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    slug = serializers.SlugField(max_length=200)
    archive = serializers.JSONField()


class ImportedEventOutput(serializers.Serializer):
    public_id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()


class ArchivePreviewChange(serializers.Serializer):
    field = serializers.CharField()
    source = serializers.JSONField(allow_null=True)
    imported = serializers.JSONField(allow_null=True)


class ArchivePreviewSection(serializers.Serializer):
    section = serializers.CharField()
    source_count = serializers.IntegerField()
    imported_count = serializers.IntegerField()


class ArchivePreviewOutput(serializers.Serializer):
    format_version = serializers.IntegerField()
    mode = serializers.CharField()
    migration_steps = serializers.ListField(child=serializers.CharField())
    deprecations = serializers.ListField(child=serializers.CharField())
    event_changes = ArchivePreviewChange(many=True)
    sections = ArchivePreviewSection(many=True)
    ignored_sections = serializers.ListField(child=serializers.CharField())


class SignedArchiveOutput(serializers.Serializer):
    manifest = serializers.DictField()
    archive = serializers.DictField()
    public_key_pem = serializers.CharField()
    signature = serializers.CharField()


class SignedArchiveImportInput(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    slug = serializers.SlugField(max_length=200)
    envelope = serializers.JSONField()


ARCHIVE_MODE = OpenApiParameter("mode", str, enum=["config", "full"], default="config")


class EventArchiveExportView(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    def get_event(self):
        return get_object_or_404(
            Event, workspace=self.get_workspace(), public_id=self.kwargs["event_public_id"]
        )

    @extend_schema(responses=ArchiveOutput, parameters=[ARCHIVE_MODE])
    def get(self, request, workspace_public_id, event_public_id):
        mode = request.query_params.get("mode", "config")
        if mode not in ("config", "full"):
            raise ValidationError({"mode": "mode must be 'config' or 'full'."})
        return Response(build_archive(self.get_event(), mode=mode))


class EventSignedArchiveExportView(EventArchiveExportView):
    @extend_schema(responses=SignedArchiveOutput, parameters=[ARCHIVE_MODE])
    def get(self, request, workspace_public_id, event_public_id):
        mode = request.query_params.get("mode", "config")
        if mode not in ("config", "full"):
            raise ValidationError({"mode": "mode must be 'config' or 'full'."})
        return Response(sign_archive(build_archive(self.get_event(), mode=mode)))


class WorkspaceArchivePreviewView(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(request=ArchiveImportInput, responses=ArchivePreviewOutput)
    def post(self, request, workspace_public_id):
        data = ArchiveImportInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            result = preview_archive_import(
                workspace=self.get_workspace(),
                archive=data.validated_data["archive"],
                name=data.validated_data["name"],
                slug=data.validated_data["slug"],
            )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(result)


class WorkspaceArchiveImportView(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(request=ArchiveImportInput, responses={201: ImportedEventOutput})
    def post(self, request, workspace_public_id):
        data = ArchiveImportInput(data=request.data)
        data.is_valid(raise_exception=True)
        return _import_event(request, self.get_workspace(), **data.validated_data)


class WorkspaceSignedArchiveImportView(WorkspaceArchiveImportView):
    @extend_schema(request=SignedArchiveImportInput, responses={201: ImportedEventOutput})
    def post(self, request, workspace_public_id):
        data = SignedArchiveImportInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            archive = verify_signed_archive(data.validated_data["envelope"])
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return _import_event(
            request,
            self.get_workspace(),
            archive=archive,
            name=data.validated_data["name"],
            slug=data.validated_data["slug"],
        )


def _import_event(request, workspace, *, archive, name, slug):
    try:
        with transaction.atomic():
            event = import_archive(workspace=workspace, archive=archive, name=name, slug=slug)
            record_mutation(
                actor=request.user,
                workspace=workspace,
                action="event.archive_imported",
                target=event,
                event_type="event.archive_imported",
                payload={"event": str(event.public_id)},
            )
    except ModelValidationError as exc:
        raise ValidationError(
            exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        ) from exc
    return Response(
        {"public_id": event.public_id, "name": event.name, "slug": event.slug}, status=201
    )
