"""The read-only extensions inventory (PD-F002-B02-T08): what this deployment's code provides."""

from accounts.authentication import CookieSessionAuthentication
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role

from . import manifest
from .mixins import WorkspaceLookupMixin
from .permissions import require_roles


class ManifestProvidesSchema(serializers.Serializer):
    kind = serializers.CharField()
    id = serializers.CharField()
    label = serializers.CharField()
    state = serializers.ChoiceField(choices=["live", "declared", "missing"])


class ManifestRequiresSchema(serializers.Serializer):
    kind = serializers.CharField()
    id = serializers.CharField()


class ManifestSchema(serializers.Serializer):
    id = serializers.CharField()
    version = serializers.CharField()
    label = serializers.CharField()
    api_version = serializers.IntegerField()
    provides = ManifestProvidesSchema(many=True)
    requires = ManifestRequiresSchema(many=True)


class CapabilityEntrySchema(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    manifest = serializers.CharField(allow_null=True)


class CapabilitySchema(serializers.Serializer):
    kind = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()
    declared_only = serializers.BooleanField()
    entries = CapabilityEntrySchema(many=True)


class ManifestProblemSchema(serializers.Serializer):
    code = serializers.CharField()
    severity = serializers.ChoiceField(choices=["error", "warning"])
    manifest = serializers.CharField(allow_null=True)
    message = serializers.CharField()


class ExtensionsSchema(serializers.Serializer):
    api_version = serializers.IntegerField()
    supported_api_versions = serializers.ListField(child=serializers.IntegerField())
    manifests = ManifestSchema(many=True)
    capabilities = CapabilitySchema(many=True)
    problems = ManifestProblemSchema(many=True)
    ok = serializers.BooleanField()


class ExtensionsView(WorkspaceLookupMixin, APIView):
    """Organizers and admins of the workspace may read it; there is no write."""

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(responses=ExtensionsSchema)
    def get(self, request, workspace_public_id):
        response = Response(manifest.snapshot())
        response["Cache-Control"] = "private, no-store"
        return response
