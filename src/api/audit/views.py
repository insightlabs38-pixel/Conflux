from accounts.authentication import CookieSessionAuthentication
from core.mixins import WorkspaceLookupMixin
from core.permissions import require_roles
from drf_spectacular.utils import extend_schema
from events.views import OrganizerView
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role

from .models import AuditEvent
from .serializers import AuditEventSchema, ConfigHistoryEntrySchema


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


class EventConfigHistoryView(OrganizerView):
    """Readable event/stage/policy/rubric configuration history (S18):
    only audit rows that actually captured a field-level diff, newest
    first. Rows written before this batch have an action name but no
    `changes` in their metadata -- those are omitted rather than shown
    with an invented or missing diff.
    """

    @extend_schema(responses=ConfigHistoryEntrySchema(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        rows = (
            AuditEvent.objects.filter(
                workspace=self.get_workspace(), metadata__event_id=str(event.public_id)
            )
            .select_related("actor")
            .order_by("-created_at", "-id")
        )
        return Response(
            [
                {
                    "public_id": str(row.public_id),
                    "actor": row.actor.username if row.actor_id else None,
                    "action": row.action,
                    "resource_type": row.target_type,
                    "resource_id": row.target_id,
                    "changes": row.metadata["changes"],
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
                if row.metadata.get("changes")
            ]
        )
