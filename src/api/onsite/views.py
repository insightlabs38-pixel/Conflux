import io

import segno
from accounts.authentication import CookieSessionAuthentication
from accounts.models import User
from audit.services import record_mutation
from core.authz import has_any_role
from core.permissions import IsWorkspaceMember, require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from events.models import Event, EventStatus, ParticipantCheckIn
from events.views import OrganizerView
from projects.models import Project, ProjectMembership
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Membership, Role, Workspace

from . import passes
from .models import Attendance, AttendanceMode, Location, LocationKind, ProjectLocation

STAFF = (Role.VOLUNTEER, Role.ORGANIZER, Role.ADMIN)


class StrictInput(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, dict) and data.keys() - self.fields.keys():
            raise ValidationError({"non_field_errors": ["Unknown fields."]})
        return super().to_internal_value(data)


class LocationInput(StrictInput):
    kind = serializers.ChoiceField(choices=LocationKind.choices)
    name = serializers.CharField(max_length=80)
    parent = serializers.UUIDField(allow_null=True, required=False)
    capacity = serializers.IntegerField(
        min_value=1, max_value=1000, allow_null=True, required=False
    )
    x = serializers.FloatField(allow_null=True, required=False)
    y = serializers.FloatField(allow_null=True, required=False)
    notes = serializers.CharField(max_length=200, allow_blank=True, required=False)
    position = serializers.IntegerField(min_value=0, max_value=100000, required=False)


class LocationPatchInput(LocationInput):
    kind = serializers.ChoiceField(choices=LocationKind.choices, required=False)
    name = serializers.CharField(max_length=80, required=False)


class LocationOutput(serializers.Serializer):
    public_id = serializers.UUIDField()
    kind = serializers.CharField()
    name = serializers.CharField()
    parent = serializers.UUIDField(allow_null=True)
    capacity = serializers.IntegerField(allow_null=True)
    x = serializers.FloatField(allow_null=True)
    y = serializers.FloatField(allow_null=True)
    notes = serializers.CharField()
    position = serializers.IntegerField()
    assigned = serializers.IntegerField()


class PlacementInput(StrictInput):
    location = serializers.UUIDField(allow_null=True)


class ApplyInput(StrictInput):
    apply = serializers.BooleanField(default=False)
    kind = serializers.ChoiceField(
        choices=[LocationKind.TABLE, LocationKind.BOOTH], default="table"
    )


class AttendanceInput(StrictInput):
    mode = serializers.ChoiceField(choices=AttendanceMode.choices)


class ScanInput(StrictInput):
    token = serializers.CharField(max_length=200)


def _errors(exc):
    return ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


class Base(APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

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

    def has_role(self, request, *roles):
        return has_any_role(request.user, self.get_workspace(), *roles)

    def ensure_mutable(self, event):
        if event.status == EventStatus.ARCHIVED:
            raise ValidationError({"status": "Archived events cannot be changed."})


class OrganizerBase(OrganizerView):
    pass


def _location_data(location, counts):
    return {
        "public_id": location.public_id,
        "kind": location.kind,
        "name": location.name,
        "parent": location.parent.public_id if location.parent_id else None,
        "capacity": location.capacity,
        "x": location.x,
        "y": location.y,
        "notes": location.notes,
        "position": location.position,
        "assigned": counts.get(location.pk, 0),
    }


def _counts(event):
    return dict(
        ProjectLocation.objects.filter(location__event=event)
        .values_list("location")
        .annotate(n=Count("pk"))
    )


def _capacity(location):
    return location.capacity or 1 if location.kind != LocationKind.ROOM else location.capacity


class LocationListView(Base):
    @extend_schema(responses=LocationOutput(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        counts = _counts(event)
        rows = Location.objects.filter(event=event).select_related("parent")
        return Response(
            LocationOutput([_location_data(item, counts) for item in rows], many=True).data
        )

    @extend_schema(request=LocationInput, responses={201: LocationOutput})
    def post(self, request, workspace_public_id, event_public_id):
        if not self.has_role(request, Role.ORGANIZER, Role.ADMIN):
            raise PermissionDenied()
        data = LocationInput(data=request.data)
        data.is_valid(raise_exception=True)
        fields = dict(data.validated_data)
        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=self.get_event().pk)
            self.ensure_mutable(event)
            parent = fields.pop("parent", None)
            location = Location(event=event, **fields)
            if parent:
                location.parent = get_object_or_404(Location, event=event, public_id=parent)
            if location.kind != LocationKind.ROOM and location.capacity is None:
                location.capacity = 1
            try:
                location.full_clean()
                location.save()
            except ModelValidationError as exc:
                raise _errors(exc) from exc
            record_mutation(
                actor=request.user,
                workspace=event.workspace,
                action="onsite.location_created",
                target=location,
                metadata={
                    "event_id": str(event.public_id),
                    "kind": location.kind,
                    "name": location.name,
                },
            )
        return Response(LocationOutput(_location_data(location, {})).data, status=201)


class LocationDetailView(OrganizerBase):
    def get_location(self, event):
        return get_object_or_404(
            Location.objects.select_for_update(of=("self",)).select_related("parent"),
            event=event,
            public_id=self.kwargs["location_public_id"],
        )

    @extend_schema(request=LocationPatchInput, responses=LocationOutput)
    def patch(self, request, workspace_public_id, event_public_id, location_public_id):
        data = LocationPatchInput(data=request.data)
        data.is_valid(raise_exception=True)
        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=self.get_event().pk)
            self.ensure_mutable(event)
            location = self.get_location(event)
            fields = dict(data.validated_data)
            if "parent" in fields:
                parent = fields.pop("parent")
                location.parent = (
                    get_object_or_404(Location, event=event, public_id=parent) if parent else None
                )
            if (
                "kind" in fields
                and fields["kind"] != location.kind
                and (location.projects.exists() or location.children.exists())
            ):
                raise ValidationError({"kind": "A location in use cannot change kind."})
            for name, value in fields.items():
                setattr(location, name, value)
            counts = _counts(event)
            if location.capacity is not None and counts.get(location.pk, 0) > location.capacity:
                raise ValidationError(
                    {"capacity": "Capacity is below the projects already placed."}
                )
            try:
                location.full_clean()
                location.save()
            except ModelValidationError as exc:
                raise _errors(exc) from exc
            record_mutation(
                actor=request.user,
                workspace=event.workspace,
                action="onsite.location_updated",
                target=location,
                metadata={"event_id": str(event.public_id), "fields": sorted(fields)},
            )
        return Response(LocationOutput(_location_data(location, counts)).data)

    @extend_schema(responses={204: None})
    def delete(self, request, workspace_public_id, event_public_id, location_public_id):
        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=self.get_event().pk)
            self.ensure_mutable(event)
            location = self.get_location(event)
            if location.projects.exists() or location.children.exists():
                raise ValidationError("Move projects and child locations out before deleting.")
            record_mutation(
                actor=request.user,
                workspace=event.workspace,
                action="onsite.location_deleted",
                target=location,
                metadata={"event_id": str(event.public_id), "name": location.name},
            )
            location.delete()
        return Response(status=204)


def _place(event, project, location_public_id, actor):
    """Place (or clear) one project inside the caller's transaction."""
    current = ProjectLocation.objects.filter(project=project).first()
    if location_public_id is None:
        if current:
            current.delete()
        return None
    location = get_object_or_404(
        Location.objects.select_for_update(), event=event, public_id=location_public_id
    )
    if location.kind == LocationKind.ROOM:
        raise ValidationError({"location": "Projects are placed at a table or booth."})
    used = ProjectLocation.objects.filter(location=location).exclude(project=project).count()
    if used >= _capacity(location):
        raise ValidationError({"location": "That location is full."})
    if current:
        current.location = location
        current.save()
        return current
    return ProjectLocation.objects.create(project=project, location=location)


class ProjectLocationListView(Base):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        rows = ProjectLocation.objects.filter(project__event=event).select_related(
            "project", "location", "location__parent"
        )
        if not self.has_role(request, Role.ORGANIZER, Role.ADMIN, Role.VOLUNTEER, Role.JUDGE):
            rows = rows.filter(project__memberships__user=request.user)
        return Response(
            [
                {
                    "project": str(row.project.public_id),
                    "project_name": row.project.name,
                    "location": str(row.location.public_id),
                    "location_name": row.location.name,
                    "kind": row.location.kind,
                    "room": row.location.parent.name if row.location.parent_id else None,
                }
                for row in rows.order_by("location__position", "location__name", "pk")
            ]
        )


class ProjectLocationView(OrganizerBase):
    @extend_schema(request=PlacementInput, responses=OpenApiTypes.OBJECT)
    def put(self, request, workspace_public_id, event_public_id, project_public_id):
        data = PlacementInput(data=request.data)
        data.is_valid(raise_exception=True)
        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=self.get_event().pk)
            self.ensure_mutable(event)
            project = get_object_or_404(Project, event=event, public_id=project_public_id)
            before = getattr(getattr(project, "location_assignment", None), "location", None)
            target = data.validated_data["location"]
            try:
                placed = _place(event, project, target, request.user)
            except ModelValidationError as exc:
                raise _errors(exc) from exc
            record_mutation(
                actor=request.user,
                workspace=event.workspace,
                action="onsite.project_placed",
                target=project,
                metadata={
                    "event_id": str(event.public_id),
                    "before": str(before.public_id) if before else None,
                    "after": str(target) if target else None,
                },
            )
        return Response(
            {"project": str(project.public_id), "location": str(target) if placed else None}
        )


class AutoAssignView(OrganizerBase):
    @extend_schema(request=ApplyInput, responses=OpenApiTypes.OBJECT)
    def post(self, request, workspace_public_id, event_public_id):
        data = ApplyInput(data=request.data)
        data.is_valid(raise_exception=True)
        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=self.get_event().pk)
            self.ensure_mutable(event)
            in_person = set(
                Attendance.objects.filter(event=event, mode=AttendanceMode.IN_PERSON).values_list(
                    "user_id", flat=True
                )
            )
            placed = set(
                ProjectLocation.objects.filter(project__event=event).values_list(
                    "project_id", flat=True
                )
            )
            projects = [
                p
                for p in Project.objects.filter(event=event)
                .exclude(pk__in=placed)
                .select_related("track")
                .order_by("track__position", "name", "pk")
                if ProjectMembership.objects.filter(project=p, user_id__in=in_person).exists()
            ]
            counts = _counts(event)
            slots = []
            for location in Location.objects.select_for_update().filter(
                event=event, kind=data.validated_data["kind"]
            ):
                slots += [location] * max(0, _capacity(location) - counts.get(location.pk, 0))
            plan = list(zip(projects, slots))
            if data.validated_data["apply"]:
                for project, location in plan:
                    ProjectLocation.objects.create(project=project, location=location)
                record_mutation(
                    actor=request.user,
                    workspace=event.workspace,
                    action="onsite.auto_assigned",
                    target=event,
                    metadata={"event_id": str(event.public_id), "placed": len(plan)},
                )
        return Response(
            {
                "applied": data.validated_data["apply"],
                "assignments": [
                    {"project": str(p.public_id), "location": str(loc.public_id)} for p, loc in plan
                ],
                "unplaced": [str(p.public_id) for p in projects[len(plan) :]],
            }
        )


class MyAttendanceView(Base):
    permission_classes = [require_roles(Role.PARTICIPANT)]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, workspace_public_id, event_public_id):
        row = Attendance.objects.filter(event=self.get_event(), user=request.user).first()
        return Response({"mode": row.mode if row else None})

    @extend_schema(request=AttendanceInput, responses=OpenApiTypes.OBJECT)
    def put(self, request, workspace_public_id, event_public_id):
        data = AttendanceInput(data=request.data)
        data.is_valid(raise_exception=True)
        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=self.get_event().pk)
            self.ensure_mutable(event)
            Attendance.objects.update_or_create(
                event=event, user=request.user, defaults={"mode": data.validated_data["mode"]}
            )
            record_mutation(
                actor=request.user,
                workspace=event.workspace,
                action="onsite.rsvp",
                target=event,
                metadata={"event_id": str(event.public_id), "mode": data.validated_data["mode"]},
            )
        return Response({"mode": data.validated_data["mode"]})


class AttendanceListView(Base):
    permission_classes = [require_roles(*STAFF)]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        checked = set(
            ParticipantCheckIn.objects.filter(event=event).values_list("participant_id", flat=True)
        )
        rows = (
            Attendance.objects.filter(event=event).select_related("user").order_by("user__username")
        )
        return Response(
            [
                {
                    "person": str(r.user.public_id),
                    "username": r.user.username,
                    "mode": r.mode,
                    "checked_in": r.user_id in checked,
                }
                for r in rows
            ]
        )


class MyPassView(Base):
    permission_classes = [require_roles(Role.PARTICIPANT)]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, workspace_public_id, event_public_id):
        return Response({"token": passes.issue(self.get_event(), request.user)})


class MyPassQrView(Base):
    permission_classes = [require_roles(Role.PARTICIPANT)]

    @extend_schema(responses={(200, "image/svg+xml"): OpenApiTypes.BINARY})
    def get(self, request, workspace_public_id, event_public_id):
        buffer = io.BytesIO()
        segno.make(passes.issue(self.get_event(), request.user), error="m").save(
            buffer, kind="svg", scale=6, border=2, xmldecl=False
        )
        response = HttpResponse(buffer.getvalue(), content_type="image/svg+xml")
        response["Cache-Control"] = "private, no-store"
        return response


class ScanView(Base):
    permission_classes = [require_roles(*STAFF)]

    @extend_schema(request=ScanInput, responses=OpenApiTypes.OBJECT)
    def post(self, request, workspace_public_id, event_public_id):
        data = ScanInput(data=request.data)
        data.is_valid(raise_exception=True)
        event = self.get_event()
        user_hex = passes.verify(data.validated_data["token"], event)
        if user_hex is None:
            raise ValidationError({"token": "Invalid pass for this event."})
        participant = get_object_or_404(
            User,
            public_id=user_hex,
            memberships__workspace=event.workspace,
            memberships__role=Role.PARTICIPANT,
        )
        with transaction.atomic():
            self.ensure_mutable(event)
            existing = ParticipantCheckIn.objects.filter(
                event=event, participant=participant
            ).first()
            if existing:
                return Response(
                    {
                        "person": str(participant.public_id),
                        "username": participant.username,
                        "already_checked_in": True,
                    }
                )
            check_in = ParticipantCheckIn(
                event=event, participant=participant, checked_in_by=request.user
            )
            try:
                check_in.full_clean()
                check_in.save()
            except ModelValidationError as exc:
                raise _errors(exc) from exc
            Attendance.objects.filter(
                event=event, user=participant, mode=AttendanceMode.REMOTE
            ).update(mode=AttendanceMode.IN_PERSON)
            record_mutation(
                actor=request.user,
                workspace=event.workspace,
                action="onsite.scan_checkin",
                target=check_in,
                metadata={"event_id": str(event.public_id), "person": str(participant.public_id)},
            )
        return Response(
            {
                "person": str(participant.public_id),
                "username": participant.username,
                "already_checked_in": False,
            }
        )


class SummaryView(Base):
    permission_classes = [require_roles(*STAFF)]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        modes = dict(
            Attendance.objects.filter(event=event).values_list("mode").annotate(n=Count("pk"))
        )
        counts = _counts(event)
        locations = list(
            Location.objects.filter(event=event, kind__in=[LocationKind.TABLE, LocationKind.BOOTH])
        )
        slots = sum(_capacity(item) for item in locations)
        participants = Membership.objects.filter(
            workspace=event.workspace, role=Role.PARTICIPANT
        ).count()
        return Response(
            {
                "participants": participants,
                "rsvp": {mode: modes.get(mode, 0) for mode in AttendanceMode.values},
                "no_response": participants - sum(modes.values()),
                "checked_in": ParticipantCheckIn.objects.filter(event=event).count(),
                "projects": Project.objects.filter(event=event).count(),
                "projects_placed": sum(counts.values()),
                "slots": slots,
                "slots_free": slots - sum(counts.get(item.pk, 0) for item in locations),
            }
        )
