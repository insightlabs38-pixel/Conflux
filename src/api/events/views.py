from accounts.authentication import CookieSessionAuthentication
from audit.services import diff_snapshots, record_mutation, snapshot_fields
from core.idempotency import IdempotentMixin
from core.permissions import IsWorkspaceMember, require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from eventconfig.consequences import audit_snapshot, preview, refusal_detail
from eventconfig.readiness import compute_readiness, configuration_checks, unresolved
from eventconfig.services import derive_event_slug
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role, Workspace

from .models import STATUS_FLOW, Announcement, BasePrize, Event, EventStatus, Track
from .schema import EventDashboardSchema, EventStatusSchema, PublicEventSchema
from .serializers import (
    AnnouncementSerializer,
    BasePrizeSerializer,
    EventCreateSerializer,
    EventSerializer,
    TrackSerializer,
)


def _save(serializer, *, actor, workspace, action, event=None, diff_fields=None, **save_kwargs):
    # `diff_fields` is only meaningful for an update (serializer.instance
    # already set) -- a create has no "before" to diff against.
    before = (
        snapshot_fields(serializer.instance, diff_fields)
        if diff_fields and serializer.instance is not None
        else None
    )
    try:
        with transaction.atomic():
            instance = serializer.save(**save_kwargs)
            instance.full_clean()
            instance.save()
            metadata = {"event_id": str((event or instance).public_id)}
            if before is not None:
                changes = diff_snapshots(before, snapshot_fields(instance, diff_fields))
                if changes:
                    metadata["changes"] = changes
            record_mutation(
                actor=actor,
                workspace=workspace,
                action=action,
                target=instance,
                event_type=action,
                payload={"event": str((event or instance).public_id)},
                metadata=metadata,
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
    serializer_class = EventSerializer

    @extend_schema(responses=EventSerializer(many=True))
    def get(self, request, workspace_public_id):
        events = Event.objects.filter(workspace=self.get_workspace())
        return Response(EventSerializer(events, many=True).data)

    @extend_schema(request=EventCreateSerializer, responses={201: EventSerializer})
    def post(self, request, workspace_public_id):
        data = request.data
        if isinstance(data, dict) and not data.get("slug") and str(data.get("name", "")).strip():
            # The address is derived from the name unless the organizer chose one (eventconfig).
            data = {**data, "slug": derive_event_slug(self.get_workspace(), data["name"])}
        serializer = EventCreateSerializer(data=data)
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
    serializer_class = EventSerializer

    def get(self, request, workspace_public_id, event_public_id):
        return Response(EventSerializer(self.get_event()).data)

    def patch(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        if event.status == EventStatus.ARCHIVED:
            raise ValidationError({"status": "Archived events cannot be edited."})
        serializer = EventSerializer(event, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        event = _save(
            serializer,
            actor=request.user,
            workspace=self.get_workspace(),
            action="event.updated",
            diff_fields=list(serializer.validated_data.keys()),
        )
        return Response(EventSerializer(event).data)

    def delete(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        shown = preview("event.delete", event)
        if not shown["allowed"]:
            raise ValidationError(refusal_detail(shown))
        with transaction.atomic():
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="event.deleted",
                target=event,
                event_type="event.deleted",
                payload={"event": str(event.public_id)},
                metadata={"consequences": audit_snapshot(shown)},
            )
            event.delete()
        return Response(status=204)


class EventStatusView(OrganizerView):
    serializer_class = EventSerializer
    transitions = STATUS_FLOW

    @extend_schema(
        request=inline_serializer(
            "EventStatusInput", fields={"status": serializers.ChoiceField(EventStatus.choices)}
        ),
        responses=EventStatusSchema,
    )
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
        readiness = compute_readiness(event) if target == EventStatus.OPEN else None
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
                    # Opening is advisory-gated: what was still unresolved is on the record.
                    metadata={"unresolved": unresolved(readiness)} if readiness else None,
                )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        body = EventSerializer(event).data
        if readiness:
            body = {**body, "readiness": readiness}
        return Response(body)


class EventDashboardView(OrganizerView):
    @extend_schema(responses=EventDashboardSchema)
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        return Response(
            {
                "event": EventSerializer(event).data,
                "track_count": event.tracks.count(),
                "base_prize_count": event.base_prizes.count(),
                # A projection of the canonical readiness rules (eventconfig/readiness.py).
                "configuration_checks": configuration_checks(compute_readiness(event)),
            }
        )


class TrackListView(OrganizerView):
    serializer_class = TrackSerializer

    def get_permissions(self):
        # Any workspace member may read the track list (e.g. a participant
        # choosing their project's track); only organizers may create one.
        if self.request.method == "GET":
            return [IsWorkspaceMember()]
        return super().get_permissions()

    @extend_schema(responses=TrackSerializer(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        return Response(TrackSerializer(self.get_event().tracks.all(), many=True).data)

    @extend_schema(responses={201: TrackSerializer})
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
    serializer_class = TrackSerializer

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
        shown = preview("track.delete", track.event, track)
        with transaction.atomic():
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="track.deleted",
                target=track,
                event_type="track.deleted",
                payload={"event": str(track.event.public_id)},
                metadata={"consequences": audit_snapshot(shown)},
            )
            track.delete()
        return Response(status=204)


class BasePrizeListView(OrganizerView):
    serializer_class = BasePrizeSerializer

    def get(self, request, workspace_public_id, event_public_id):
        return Response(BasePrizeSerializer(self.get_event().base_prizes.all(), many=True).data)

    @extend_schema(responses={201: BasePrizeSerializer})
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
    serializer_class = BasePrizeSerializer

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
        shown = preview("base_prize.delete", prize.event, prize)
        with transaction.atomic():
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="base_prize.deleted",
                target=prize,
                event_type="base_prize.deleted",
                payload={"event": str(prize.event.public_id)},
                metadata={"consequences": audit_snapshot(shown)},
            )
            prize.delete()
        return Response(status=204)


class AnnouncementListView(IdempotentMixin, OrganizerView):
    serializer_class = AnnouncementSerializer

    @extend_schema(responses=AnnouncementSerializer(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        announcements = Announcement.objects.filter(event=self.get_event()).select_related(
            "posted_by"
        )
        return Response(AnnouncementSerializer(announcements, many=True).data)

    @extend_schema(responses={201: AnnouncementSerializer})
    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        self.ensure_mutable(event)
        serializer = AnnouncementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        announcement = _save(
            serializer,
            actor=request.user,
            workspace=self.get_workspace(),
            action="announcement.posted",
            event=event,
            event_id=event.id,
            posted_by=request.user,
        )
        return Response(AnnouncementSerializer(announcement).data, status=201)


class AnnouncementDetailView(OrganizerView):
    serializer_class = AnnouncementSerializer

    def delete(self, request, workspace_public_id, event_public_id, announcement_public_id):
        announcement = get_object_or_404(
            Announcement, event=self.get_event(), public_id=announcement_public_id
        )
        with transaction.atomic():
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="announcement.deleted",
                target=announcement,
                event_type="announcement.deleted",
                payload={"event": str(announcement.event.public_id)},
            )
            announcement.delete()
        return Response(status=204)


class PublicEventView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=PublicEventSchema)
    def get(self, request, event_public_id):
        from presentation.models import Page
        from presentation.public import get_public_event
        from presentation.themes import resolved_theme

        event = get_public_event(event_public_id)
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
                "presentation": resolved_theme(Page.objects.filter(event=event).first()),
                "tracks": TrackSerializer(event.tracks.all(), many=True).data,
                "base_prizes": BasePrizeSerializer(
                    event.base_prizes.select_related("track"), many=True
                ).data,
            }
        )
