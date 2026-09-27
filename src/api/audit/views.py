from accounts.authentication import CookieSessionAuthentication
from core.mixins import WorkspaceLookupMixin
from core.permissions import require_roles
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role

from .models import AuditEvent
from .serializers import AuditEventSchema


def _serialize(event):
    return {
        "public_id": str(event.public_id),
        "actor": event.actor.username if event.actor_id else None,
        "action": event.action,
        "target_type": event.target_type,
        "target_id": event.target_id,
        "metadata": event.metadata,
        "created_at": event.created_at.isoformat(),
    }


class WorkspaceAuditLogView(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(responses=AuditEventSchema(many=True))
    def get(self, request, workspace_public_id):
        events = AuditEvent.objects.filter(workspace=self.get_workspace())
        return Response([_serialize(e) for e in events])
