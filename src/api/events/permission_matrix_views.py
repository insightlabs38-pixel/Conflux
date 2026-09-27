"""VS25/VS26: permission matrix explorer and authorization dry-run --
organizer-only, since these expose the platform's internal authorization
structure. The event in the URL is where an organizer finds these tools
(alongside their other event dashboards); the underlying data is
workspace/event-independent for the matrix, and workspace-scoped (real
Membership rows) for the dry run.
"""

from accounts.models import User
from core.permission_matrix import build_permission_matrix, dry_run
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from workspaces.models import Role

from .views import OrganizerView


class PermissionMatrixEntrySchema(serializers.Serializer):
    resource = serializers.CharField()
    view = serializers.CharField()
    path = serializers.CharField()
    method = serializers.CharField()
    access = serializers.ChoiceField(choices=["roles", "any_authenticated", "public", "unknown"])
    roles = serializers.ListField(child=serializers.CharField())
    unrecognized = serializers.BooleanField()


class PermissionMatrixView(OrganizerView):
    serializer_class = PermissionMatrixEntrySchema

    @extend_schema(responses=PermissionMatrixEntrySchema(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        return Response(build_permission_matrix())


class AuthzDryRunInputSchema(serializers.Serializer):
    path = serializers.CharField()
    method = serializers.ChoiceField(choices=["GET", "POST", "PUT", "PATCH", "DELETE"])
    subject_kind = serializers.ChoiceField(choices=["role", "user"])
    subject = serializers.CharField()


class AuthzDryRunOutputSchema(serializers.Serializer):
    allowed = serializers.BooleanField()
    mode = serializers.ChoiceField(choices=["live", "hypothetical"])
    access = serializers.CharField(required=False)
    roles = serializers.ListField(child=serializers.CharField(), required=False)
    actual_roles = serializers.ListField(child=serializers.CharField(), required=False)


class AuthzDryRunView(OrganizerView):
    """Never calls the target endpoint's real handler -- only its
    `get_permissions()`/`has_permission()` gate. See `core.permission_
    matrix.dry_run` for exactly what "live" vs. "hypothetical" means.
    """

    serializer_class = AuthzDryRunOutputSchema

    @extend_schema(request=AuthzDryRunInputSchema, responses=AuthzDryRunOutputSchema)
    def post(self, request, workspace_public_id, event_public_id):
        serializer = AuthzDryRunInputSchema(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        workspace = self.get_workspace()

        if data["subject_kind"] == "role":
            if data["subject"] not in Role.values:
                raise ValidationError({"subject": "Unknown role."})
            subject = data["subject"]
        else:
            subject = get_object_or_404(User, public_id=data["subject"])

        result = dry_run(
            path=data["path"],
            method=data["method"],
            workspace=workspace,
            subject_kind=data["subject_kind"],
            subject=subject,
        )
        if "error" in result:
            raise ValidationError({"path": result["error"]})
        return Response(result)
