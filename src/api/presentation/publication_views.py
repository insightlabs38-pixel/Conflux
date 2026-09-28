from datetime import UTC

from audit.services import diff_snapshots, record_mutation, snapshot_fields
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import OpenApiParameter, extend_schema
from events.models import Event
from events.views import OrganizerView
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from stages.models import Stage

from .models import PublicationSchedule, PublicationSurface
from .public import get_public_event, public_projects
from .public_api import GalleryItemOutput, gallery_items
from .publication import schedule_is_open


class PublicationInput(serializers.Serializer):
    opens_at = serializers.DateTimeField(default_timezone=UTC)
    closes_at = serializers.DateTimeField(default_timezone=UTC, allow_null=True, default=None)
    finalist_stage = serializers.UUIDField(allow_null=True, default=None)

    def validate(self, attrs):
        if self.initial_data.keys() - self.fields.keys():
            raise ValidationError("Unknown fields.")
        for field in ("opens_at", "closes_at"):
            value = self.initial_data.get(field)
            if value is not None:
                raw = parse_datetime(value) if isinstance(value, str) else value
                if raw is None or timezone.is_naive(raw):
                    raise ValidationError({field: "Include an explicit UTC offset."})
        if attrs["closes_at"] is not None and attrs["closes_at"] <= attrs["opens_at"]:
            raise ValidationError({"closes_at": "Close must be after open."})
        stage_id = attrs["finalist_stage"]
        if self.context["surface"] == PublicationSurface.FINALISTS:
            stage = Stage.objects.filter(event=self.context["event"], public_id=stage_id).first()
            if stage is None:
                raise ValidationError({"finalist_stage": "Select a stage in this event."})
            attrs["finalist_stage"] = stage
        elif stage_id is not None:
            raise ValidationError({"finalist_stage": "Only finalists use a stage."})
        return attrs


class PublicationOutput(serializers.ModelSerializer):
    opens_at = serializers.DateTimeField(default_timezone=UTC)
    closes_at = serializers.DateTimeField(default_timezone=UTC, allow_null=True)
    finalist_stage = serializers.UUIDField(source="finalist_stage.public_id", allow_null=True)

    class Meta:
        model = PublicationSchedule
        fields = ["surface", "opens_at", "closes_at", "finalist_stage", "updated_at"]
        read_only_fields = fields


class PublicationListView(OrganizerView):
    @extend_schema(responses=PublicationOutput(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        return Response(
            PublicationOutput(self.get_event().publication_schedules.all(), many=True).data
        )


@extend_schema(parameters=[OpenApiParameter("surface", str, enum=PublicationSurface.values)])
class PublicationDetailView(OrganizerView):
    def surface(self):
        value = self.kwargs["surface"]
        if value not in PublicationSurface.values:
            raise ValidationError({"surface": "Unknown publication surface."})
        return value

    @extend_schema(request=PublicationInput, responses=PublicationOutput)
    def put(self, request, workspace_public_id, event_public_id, surface):
        event = self.get_event()
        surface = self.surface()
        data = PublicationInput(data=request.data, context={"event": event, "surface": surface})
        data.is_valid(raise_exception=True)
        fields = ["opens_at", "closes_at", "finalist_stage"]
        with transaction.atomic():
            # Lock the parent even for an absent schedule, so competing first writes serialize.
            Event.objects.select_for_update().get(pk=event.pk)
            schedule = PublicationSchedule.objects.filter(event=event, surface=surface).first()
            before = snapshot_fields(schedule, fields) if schedule else None
            schedule, _ = PublicationSchedule.objects.update_or_create(
                event=event, surface=surface, defaults=data.validated_data
            )
            after = snapshot_fields(schedule, fields)
            record_mutation(
                actor=request.user,
                workspace=event.workspace,
                action="publication.schedule_saved",
                target=schedule,
                metadata={
                    "event_id": str(event.public_id),
                    "surface": surface,
                    "changes": diff_snapshots(before, after) if before else after,
                },
            )
        return Response(PublicationOutput(schedule).data)

    @extend_schema(responses={204: None})
    def delete(self, request, workspace_public_id, event_public_id, surface):
        event = self.get_event()
        surface = self.surface()
        with transaction.atomic():
            Event.objects.select_for_update().get(pk=event.pk)
            schedule = get_object_or_404(PublicationSchedule, event=event, surface=surface)
            record_mutation(
                actor=request.user,
                workspace=event.workspace,
                action="publication.schedule_removed",
                target=schedule,
                metadata={"event_id": str(event.public_id), "surface": surface},
            )
            schedule.delete()
        return Response(status=204)


def finalist_projects(event):
    schedule = get_object_or_404(
        PublicationSchedule, event=event, surface=PublicationSurface.FINALISTS
    )
    if not schedule_is_open(schedule, timezone.now()):
        raise Http404("Finalists have not been released.")
    return public_projects(event, stage_public_id=schedule.finalist_stage.public_id)


class PublicFinalistsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=GalleryItemOutput(many=True))
    def get(self, request, event_public_id):
        event = get_public_event(event_public_id)
        return Response(gallery_items(request, event, finalist_projects(event)))
