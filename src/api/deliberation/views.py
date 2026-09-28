from accounts.authentication import CookieSessionAuthentication
from awards.models import Award
from core.authz import has_any_role
from core.permissions import require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from evaluations.eligibility import eligible_projects
from events.models import Event
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role, Workspace

from . import services
from .models import DeliberationRoom, RoomStatus, Stance


class StrictInput(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, dict) and data.keys() - self.fields.keys():
            raise ValidationError({"non_field_errors": ["Unknown fields."]})
        return super().to_internal_value(data)


class OpenInput(StrictInput):
    quorum = serializers.IntegerField(min_value=1, max_value=200, required=False)


class NoteInput(StrictInput):
    body = serializers.CharField(max_length=2000)
    project = serializers.UUIDField(required=False)


class StanceInput(StrictInput):
    stance = serializers.ChoiceField(choices=Stance.choices)
    rationale = serializers.CharField(max_length=500, allow_blank=True, default="")


class FinalizeInput(StrictInput):
    winners = serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=50)
    override_reason = serializers.CharField(max_length=1000, allow_blank=True, default="")


class RoomOutput(serializers.Serializer):
    public_id = serializers.UUIDField()
    status = serializers.CharField()
    quorum = serializers.IntegerField()
    notes = serializers.ListField(child=serializers.DictField())
    stances = serializers.ListField(child=serializers.DictField())
    tally = serializers.ListField(child=serializers.DictField())
    finalization = serializers.DictField()


def _errors(exc):
    return ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


class RoomBase(APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    def get_workspace(self):
        return get_object_or_404(Workspace, public_id=self.kwargs["workspace_public_id"])

    def get_award(self):
        event = get_object_or_404(
            Event, workspace=self.get_workspace(), public_id=self.kwargs["event_public_id"]
        )
        return get_object_or_404(Award, event=event, public_id=self.kwargs["award_public_id"])

    def is_organizer(self, request):
        return has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN)

    def require_organizer(self, request):
        if not self.is_organizer(request):
            raise PermissionDenied("Only organizers can do this.")

    def get_room(self, request):
        award = self.get_award()
        room = DeliberationRoom.objects.filter(award=award).select_related("award").first()
        if room is None:
            raise NotFound("No deliberation room for this award.")
        if not self.is_organizer(request) and not services.is_panelist(room, request.user):
            raise NotFound("No deliberation room for this award.")
        return room


def _room_data(room, user, organizer):
    plan = room.award.evaluation_plan
    visible = (
        None
        if organizer
        else {p.pk for p in eligible_projects(plan) if services.has_evaluated(plan, user, p)}
    )

    def allowed(project_id):
        return organizer or project_id is None or project_id in visible

    notes = [
        {
            "public_id": str(n.public_id),
            "project": str(n.project.public_id) if n.project_id else None,
            "author": n.author.username,
            "body": n.body,
            "created_at": n.created_at,
        }
        for n in room.notes.select_related("project", "author")
        if allowed(n.project_id)
    ]
    stances = [
        {
            "project": str(s.project.public_id),
            "judge": s.judge.username,
            "stance": s.stance,
            "rationale": s.rationale,
        }
        for s in room.stances.select_related("project", "judge")
        if allowed(s.project_id)
    ]
    allowed_projects = {s["project"] for s in stances}
    tally = [row for row in services.tally(room) if organizer or row["project"] in allowed_projects]
    return {
        "public_id": room.public_id,
        "status": room.status,
        "quorum": room.quorum,
        "notes": notes,
        "stances": stances,
        "tally": tally,
        "finalization": room.finalization
        if organizer or room.status == RoomStatus.FINALIZED
        else {},
    }


class RoomView(RoomBase):
    @extend_schema(responses=RoomOutput)
    def get(self, request, workspace_public_id, event_public_id, award_public_id):
        room = self.get_room(request)
        return Response(RoomOutput(_room_data(room, request.user, self.is_organizer(request))).data)

    @extend_schema(request=OpenInput, responses={201: RoomOutput})
    def post(self, request, workspace_public_id, event_public_id, award_public_id):
        self.require_organizer(request)
        data = OpenInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            room = services.open_room(
                self.get_award(), request.user, data.validated_data.get("quorum")
            )
        except ModelValidationError as exc:
            raise _errors(exc) from exc
        return Response(RoomOutput(_room_data(room, request.user, True)).data, status=201)


class NoteView(RoomBase):
    @extend_schema(request=NoteInput, responses={201: RoomOutput})
    def post(self, request, workspace_public_id, event_public_id, award_public_id):
        room = self.get_room(request)
        data = NoteInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            services.add_note(
                room,
                request.user,
                data.validated_data["body"],
                str(data.validated_data["project"]) if "project" in data.validated_data else None,
            )
        except PermissionError as exc:
            raise PermissionDenied("Evaluate this project before discussing it.") from exc
        except ModelValidationError as exc:
            raise _errors(exc) from exc
        return Response(RoomOutput(_room_data(room, request.user, False)).data, status=201)


class StanceView(RoomBase):
    @extend_schema(request=StanceInput, responses=RoomOutput)
    def put(
        self, request, workspace_public_id, event_public_id, award_public_id, project_public_id
    ):
        room = self.get_room(request)
        data = StanceInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            services.set_stance(
                room,
                request.user,
                str(project_public_id),
                data.validated_data["stance"],
                data.validated_data["rationale"],
            )
        except PermissionError as exc:
            raise PermissionDenied("Evaluate this project before taking a stance.") from exc
        except ModelValidationError as exc:
            raise _errors(exc) from exc
        return Response(RoomOutput(_room_data(room, request.user, False)).data)


class CloseView(RoomBase):
    @extend_schema(request=None, responses=RoomOutput)
    def post(self, request, workspace_public_id, event_public_id, award_public_id):
        self.require_organizer(request)
        try:
            room = services.close_room(self.get_room(request), request.user)
        except ModelValidationError as exc:
            raise _errors(exc) from exc
        return Response(RoomOutput(_room_data(room, request.user, True)).data)


class FinalizeView(RoomBase):
    @extend_schema(request=FinalizeInput, responses=RoomOutput)
    def post(self, request, workspace_public_id, event_public_id, award_public_id):
        self.require_organizer(request)
        data = FinalizeInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            room = services.finalize(
                self.get_room(request),
                request.user,
                [str(w) for w in data.validated_data["winners"]],
                data.validated_data["override_reason"],
            )
        except ModelValidationError as exc:
            raise _errors(exc) from exc
        return Response(RoomOutput(_room_data(room, request.user, True)).data)
