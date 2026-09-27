from accounts.authentication import CookieSessionAuthentication
from audit.services import record_mutation
from core.permissions import IsWorkspaceMember, require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role, Workspace

from .models import BasePrize, Event, EventStatus, Track
from .serializers import BasePrizeSerializer, EventSerializer, TrackSerializer


def _save(serializer, *, actor, workspace, action, event=None, **save_kwargs):
    try:
        with transaction.atomic():
            instance = serializer.save(**save_kwargs)
            instance.full_clean()
            instance.save()
            record_mutation(
                actor=actor,
                workspace=workspace,
                action=action,
                target=instance,
                event_type=action,
                payload={"event": str((event or instance).public_id)},
            )
    except ModelValidationError as exc:
        raise ValidationError(
            exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        ) from exc
    except IntegrityError as exc:
        raise ValidationError(
            {"detail": "A record with this name or slug already exists."}
        ) from exc
    return instance


class OrganizerView(APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    def get_workspace(self):
        if not hasattr(self, "_workspace"):
            self._workspace = get_object_or_404(
                Workspace, public_id=self.kwargs["workspace_public_id"]
            )
        return self._workspace

    def get_event(self):
        return get_object_or_404(
            Event, workspace=self.get_workspace(), public_id=self.kwargs["event_public_id"]
        )

    def ensure_mutable(self, event):
        if event.status == EventStatus.ARCHIVED:
            raise ValidationError({"status": "Archived event configuration cannot be edited."})


class EventListView(OrganizerView):
    def get(self, request, workspace_public_id):
        events = Event.objects.filter(workspace=self.get_workspace())
        return Response(EventSerializer(events, many=True).data)

    def post(self, request, workspace_public_id):
        serializer = EventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = _save(
            serializer,
            actor=request.user,
            workspace=self.get_workspace(),
            action="event.created",
            workspace_id=self.get_workspace().id,
        )
        return Response(EventSerializer(event).data, status=201)


class EventDetailView(OrganizerView):
    def get(self, request, workspace_public_id, event_public_id):
        return Response(EventSerializer(self.get_event()).data)

    def patch(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        if event.status == EventStatus.ARCHIVED:
            raise ValidationError({"status": "Archived events cannot be edited."})
        serializer = EventSerializer(event, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        event = _save(
            serializer, actor=request.user, workspace=self.get_workspace(), action="event.updated"
        )
        return Response(EventSerializer(event).data)

    def delete(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        if event.status != EventStatus.DRAFT:
            raise ValidationError({"status": "Only draft events can be deleted."})
        with transaction.atomic():
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="event.deleted",
                target=event,
                event_type="event.deleted",
                payload={"event": str(event.public_id)},
            )
            event.delete()
        return Response(status=204)


class EventStatusView(OrganizerView):
    transitions = {
        EventStatus.DRAFT: EventStatus.OPEN,
        EventStatus.OPEN: EventStatus.CLOSED,
        EventStatus.CLOSED: EventStatus.ARCHIVED,
    }

    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        target = request.data.get("status")
        if target != self.transitions.get(event.status):
            raise ValidationError(
                {"status": f"Invalid transition from {event.status} to {target}."}
            )
        if target == EventStatus.OPEN and event.ends_at and event.ends_at <= timezone.now():
            raise ValidationError({"ends_at": "An event cannot open after its end date."})
        event.status = target
        try:
            with transaction.atomic():
                event.full_clean()
                event.save(update_fields=["status", "updated_at"])
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="event.status_changed",
                    target=event,
                    event_type="event.status_changed",
                    payload={"event": str(event.public_id), "status": target},
                )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(EventSerializer(event).data)


class EventDashboardView(OrganizerView):
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        blockers = []
        if not event.starts_at or not event.ends_at:
            blockers.append("Set the event start and end dates.")
        if not event.tracks.exists():
            blockers.append("Add a track.")
        if not event.base_prizes.exists():
            blockers.append("Configure a base prize.")
        return Response(
            {
                "event": EventSerializer(event).data,
                "track_count": event.tracks.count(),
                "base_prize_count": event.base_prizes.count(),
                "configuration_checks": blockers,
            }
        )


class TrackListView(OrganizerView):
    def get_permissions(self):
        # Any workspace member may read the track list (e.g. a participant
        # choosing their project's track); only organizers may create one.
        if self.request.method == "GET":
            return [IsWorkspaceMember()]
        return super().get_permissions()

    def get(self, request, workspace_public_id, event_public_id):
        return Response(TrackSerializer(self.get_event().tracks.all(), many=True).data)

    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        self.ensure_mutable(event)
        serializer = TrackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        track = _save(
            serializer,
            actor=request.user,
            workspace=self.get_workspace(),
            action="track.created",
            event=event,
            event_id=event.id,
        )
        return Response(TrackSerializer(track).data, status=201)


class TrackDetailView(OrganizerView):
    def get_track(self):
        return get_object_or_404(
            Track, event=self.get_event(), public_id=self.kwargs["track_public_id"]
        )

    def patch(self, request, workspace_public_id, event_public_id, track_public_id):
        track = self.get_track()
        self.ensure_mutable(track.event)
        serializer = TrackSerializer(track, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        track = _save(
            serializer,
            actor=request.user,
            workspace=self.get_workspace(),
            action="track.updated",
            event=track.event,
        )
        return Response(TrackSerializer(track).data)

    def delete(self, request, workspace_public_id, event_public_id, track_public_id):
        track = self.get_track()
        self.ensure_mutable(track.event)
        with transaction.atomic():
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="track.deleted",
                target=track,
                event_type="track.deleted",
                payload={"event": str(track.event.public_id)},
            )
            track.delete()
        return Response(status=204)


class BasePrizeListView(OrganizerView):
    def get(self, request, workspace_public_id, event_public_id):
        return Response(BasePrizeSerializer(self.get_event().base_prizes.all(), many=True).data)

    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        self.ensure_mutable(event)
        serializer = BasePrizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        track_id = serializer.validated_data.pop("track", None)
        track = get_object_or_404(Track, event=event, public_id=track_id) if track_id else None
        prize = _save(
            serializer,
            actor=request.user,
            workspace=self.get_workspace(),
            action="base_prize.created",
            event=event,
            event_id=event.id,
            track=track,
        )
        return Response(BasePrizeSerializer(prize).data, status=201)


class BasePrizeDetailView(OrganizerView):
    def get_prize(self):
        return get_object_or_404(
            BasePrize, event=self.get_event(), public_id=self.kwargs["prize_public_id"]
        )

    def patch(self, request, workspace_public_id, event_public_id, prize_public_id):
        prize = self.get_prize()
        self.ensure_mutable(prize.event)
        serializer = BasePrizeSerializer(prize, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        track_id = (
            serializer.validated_data.pop("track", None)
            if "track" in serializer.validated_data
            else None
        )
        if "track" in request.data:
            prize.track = (
                get_object_or_404(Track, event=prize.event, public_id=track_id)
                if track_id
                else None
            )
        prize = _save(
            serializer,
            actor=request.user,
            workspace=self.get_workspace(),
            action="base_prize.updated",
            event=prize.event,
        )
        return Response(BasePrizeSerializer(prize).data)

    def delete(self, request, workspace_public_id, event_public_id, prize_public_id):
        prize = self.get_prize()
        self.ensure_mutable(prize.event)
        with transaction.atomic():
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="base_prize.deleted",
                target=prize,
                event_type="base_prize.deleted",
                payload={"event": str(prize.event.public_id)},
            )
            prize.delete()
        return Response(status=204)


class PublicEventView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, event_public_id):
        event = get_object_or_404(
            Event, public_id=event_public_id, is_public=True, status=EventStatus.OPEN
        )
        data = EventSerializer(event).data
        return Response(
            {
                **{
                    key: data[key]
                    for key in (
                        "public_id",
                        "name",
                        "slug",
                        "description",
                        "timezone",
                        "starts_at",
                        "ends_at",
                        "status",
                    )
                },
                "tracks": TrackSerializer(event.tracks.all(), many=True).data,
                "base_prizes": BasePrizeSerializer(
                    event.base_prizes.select_related("track"), many=True
                ).data,
            }
        )
