from accounts.authentication import CookieSessionAuthentication
from accounts.models import User
from core.permissions import IsWorkspaceMember
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from events.models import Event, EventStatus
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Workspace

from .models import TeamInvite, TeamMembership, TeamMembershipRole
from .serializers import TeamInviteSerializer, TeamSerializer
from .services import (
    create_invite,
    create_team,
    leave_team,
    redeem_invite,
    revoke_invite,
    transfer_captaincy,
)


def _as_drf_validation_error(exc):
    return ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


class ParticipantView(APIView):
    """Any workspace member (any role) may manage their own participation —
    this is not organizer-only, unlike events.views.OrganizerView.
    """

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

    def my_membership(self, event):
        return TeamMembership.objects.filter(team__event=event, user=self.request.user).first()


class ParticipantEventListView(ParticipantView):
    def get(self, request, workspace_public_id):
        events = Event.objects.filter(workspace=self.get_workspace(), is_public=True).exclude(
            status__in=[EventStatus.DRAFT, EventStatus.ARCHIVED]
        )
        return Response(
            [{"public_id": str(event.public_id), "name": event.name} for event in events]
        )


class MyTeamView(ParticipantView):
    """GET: my current team in this event, or null (the empty state — not
    yet on a team is a normal, expected status, not an error).
    """

    serializer_class = TeamSerializer

    def get(self, request, workspace_public_id, event_public_id):
        # {"team": null} on purpose, not a bare `Response(None)`: DRF
        # renders `None` data as an empty body with no Content-Type at
        # all, which isn't valid JSON a client can parse — "not yet on a
        # team" still has to be a real, decodable response.
        membership = self.my_membership(self.get_event())
        if membership is None:
            return Response({"team": None, "my_role": None})
        return Response({"team": TeamSerializer(membership.team).data, "my_role": membership.role})

    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        if self.my_membership(event) is not None:
            raise ValidationError({"detail": "Already on a team in this event."})
        name = str(request.data.get("name", "")).strip()
        if not name:
            raise ValidationError({"name": "Team name is required."})
        try:
            team = create_team(event, name, request.user)
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        except IntegrityError as exc:
            raise ValidationError({"detail": "A team with this name already exists."}) from exc
        return Response(TeamSerializer(team).data, status=201)


class LeaveTeamView(ParticipantView):
    def post(self, request, workspace_public_id, event_public_id):
        membership = self.my_membership(self.get_event())
        if membership is None:
            raise ValidationError({"detail": "Not currently on a team in this event."})
        try:
            leave_team(membership.team, request.user)
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        return Response(status=204)


class TransferCaptainView(ParticipantView):
    def post(self, request, workspace_public_id, event_public_id):
        membership = self.my_membership(self.get_event())
        if membership is None:
            raise ValidationError({"detail": "Not currently on a team in this event."})
        target_public_id = request.data.get("user")
        target = get_object_or_404(User, public_id=target_public_id)
        try:
            transfer_captaincy(membership.team, request.user, target)
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        return Response(TeamSerializer(membership.team).data)


class TeamInviteListView(ParticipantView):
    serializer_class = TeamInviteSerializer

    def get(self, request, workspace_public_id, event_public_id):
        membership = self.my_membership(self.get_event())
        if membership is None or membership.role != TeamMembershipRole.CAPTAIN:
            raise ValidationError({"detail": "Only the team captain can view invite links."})
        invites = TeamInvite.objects.filter(team=membership.team, revoked_at__isnull=True)
        return Response(TeamInviteSerializer(invites, many=True).data)

    def post(self, request, workspace_public_id, event_public_id):
        membership = self.my_membership(self.get_event())
        if membership is None:
            raise ValidationError({"detail": "Not currently on a team in this event."})
        try:
            max_uses = int(request.data.get("max_uses", 1))
        except (TypeError, ValueError) as exc:
            raise ValidationError({"max_uses": "Must be an integer."}) from exc
        try:
            invite = create_invite(membership.team, request.user, max_uses=max_uses)
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        return Response(TeamInviteSerializer(invite).data, status=201)


class TeamInviteDetailView(ParticipantView):
    def delete(self, request, workspace_public_id, event_public_id, invite_public_id):
        membership = self.my_membership(self.get_event())
        if membership is None:
            raise ValidationError({"detail": "Not currently on a team in this event."})
        invite = get_object_or_404(TeamInvite, team=membership.team, public_id=invite_public_id)
        try:
            revoke_invite(invite, request.user)
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        return Response(status=204)


class RedeemInviteView(ParticipantView):
    def post(self, request, workspace_public_id, event_public_id):
        token = str(request.data.get("token", ""))
        try:
            membership = redeem_invite(token, request.user, event=self.get_event())
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        return Response(TeamSerializer(membership.team).data, status=201)
