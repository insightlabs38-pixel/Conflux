"""VS25: permission matrix explorer -- organizer-only, since this exposes
the platform's internal authorization structure. The event in the URL is
where an organizer finds this tool (alongside their other event
dashboards); the underlying data is workspace/event-independent, since
`permission_classes` don't vary by event.
"""

from core.permission_matrix import build_permission_matrix
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response

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
