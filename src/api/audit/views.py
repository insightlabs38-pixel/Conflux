from accounts.authentication import CookieSessionAuthentication
from core.mixins import WorkspaceLookupMixin
from core.permissions import require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from events.models import BasePrize, Event, Track
from events.serializers import BasePrizeSerializer, EventSerializer, TrackSerializer
from events.views import OrganizerView
from policies.models import Policy, TemporalGate
from policies.serializers import PolicySerializer, TemporalGateSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from stages.models import Stage
from stages.serializers import StageSerializer
from workspaces.models import Role

from .models import AuditEvent
from .serializers import AuditEventSchema, ConfigHistoryEntrySchema, ConfigRestoreResultSchema
from .services import diff_snapshots, record_mutation, snapshot_fields


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


class EventConfigHistoryRestoreView(OrganizerView):
    RESTORABLE = {
        "Stage": (Stage, StageSerializer),
        "TemporalGate": (TemporalGate, TemporalGateSerializer),
        "Policy": (Policy, PolicySerializer),
        "Event": (Event, EventSerializer),
        "Track": (Track, TrackSerializer),
        "BasePrize": (BasePrize, BasePrizeSerializer),
    }

    @extend_schema(request=None, responses=ConfigRestoreResultSchema)
    @transaction.atomic
    def post(self, request, workspace_public_id, event_public_id, audit_event_public_id):
        event = Event.objects.select_for_update().get(pk=self.get_event().pk)
        self.ensure_mutable(event)
        workspace = self.get_workspace()
        row = get_object_or_404(
            AuditEvent,
            workspace=workspace,
            public_id=audit_event_public_id,
            metadata__event_id=str(event.public_id),
        )
        changes = row.metadata.get("changes")
        if not isinstance(changes, dict) or not changes:
            raise ValidationError({"detail": "Nothing to restore for this entry."})
        definition = self.RESTORABLE.get(row.target_type)
        if definition is None or not row.action.endswith((".updated", ".restored")):
            raise ValidationError({"detail": "This configuration entry cannot be restored."})
        model, serializer_type = definition
        scope = {"pk": event.pk} if model is Event else {"event": event}
        instance = get_object_or_404(
            model.objects.select_for_update(), public_id=row.target_id, **scope
        )
        writable = {
            name
            for name, field in serializer_type().fields.items()
            if not field.read_only and name not in {"preset", "preset_params"}
        }
        if not changes.keys() <= writable or any(
            not isinstance(change, dict) or "before" not in change or "after" not in change
            for change in changes.values()
        ):
            raise ValidationError({"detail": "The recorded fields cannot be restored."})
        data = {field: change["before"] for field, change in changes.items()}
        # Audit snapshots store internal FK keys; the edit API takes public IDs.
        if model is BasePrize and data.get("track") is not None:
            data["track"] = get_object_or_404(Track, event=event, pk=data["track"]).public_id
        serializer = serializer_type(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        if model is BasePrize and "track" in values:
            values["track"] = (
                get_object_or_404(Track, event=event, public_id=values["track"])
                if values["track"] is not None
                else None
            )
        fields = list(changes)
        try:
            with transaction.atomic():
                before = snapshot_fields(instance, fields)
                for field, value in values.items():
                    setattr(instance, field, value)
                instance.full_clean()
                instance.save()
                restore_changes = diff_snapshots(before, snapshot_fields(instance, fields))
                action = row.action.rsplit(".", 1)[0] + ".restored"
                record_mutation(
                    actor=request.user,
                    workspace=workspace,
                    action=action,
                    target=instance,
                    event_type=action,
                    payload={"event": str(event.public_id)},
                    metadata={
                        "event_id": str(event.public_id),
                        "changes": restore_changes,
                        "restored_from": str(row.public_id),
                    },
                )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        except IntegrityError as exc:
            raise ValidationError(
                {"detail": "Restored configuration conflicts with current state."}
            ) from exc
        return Response(
            {
                "restored": True,
                "resource_type": row.target_type,
                "resource_id": row.target_id,
                "changes": restore_changes,
            }
        )
