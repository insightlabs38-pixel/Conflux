from audit.services import record_mutation
from core.permissions import require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from projects.models import Project
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from workspaces.models import Role

from .marketplace import (
    available_openings,
    available_profiles,
    matches_for_opening,
    matches_for_participant,
    normalize_skills,
    opening_data,
    profile_data,
)
from .models import MarketplaceProfile, TeamMembershipRole, TeamOpening
from .serializers import (
    MarketplaceProfileInput,
    MarketplaceProfileSchema,
    MyMarketplaceProfileResponse,
    TeamOpeningInput,
    TeamOpeningSchema,
)
from .views import ParticipantView


def _validation_error(exc):
    return ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


class MarketplaceView(ParticipantView):
    permission_classes = [require_roles(Role.PARTICIPANT)]

    def captain_membership(self):
        membership = self.my_membership(self.get_event())
        if membership is None or membership.role != TeamMembershipRole.CAPTAIN:
            raise ValidationError({"detail": "Only a team captain can manage openings."})
        return membership


class MyMarketplaceProfileView(MarketplaceView):
    @extend_schema(responses=MyMarketplaceProfileResponse)
    def get(self, request, workspace_public_id, event_public_id):
        profile = MarketplaceProfile.objects.filter(
            event=self.get_event(), user=request.user
        ).first()
        return Response({"profile": profile_data(profile) if profile else None})

    @extend_schema(request=MarketplaceProfileInput, responses=MarketplaceProfileSchema)
    def put(self, request, workspace_public_id, event_public_id):
        serializer = MarketplaceProfileInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            skills = normalize_skills(data["skills"])
            with transaction.atomic():
                profile, _ = MarketplaceProfile.objects.select_for_update().get_or_create(
                    event=self.get_event(), user=request.user
                )
                profile.skills = skills
                profile.bio = data.get("bio", "")
                profile.visible = data["visible"]
                profile.full_clean()
                profile.save()
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="marketplace.profile_updated",
                    target=profile,
                )
        except ModelValidationError as exc:
            raise _validation_error(exc) from exc
        return Response(profile_data(profile))


class MarketplaceProfilesView(MarketplaceView):
    @extend_schema(responses=MarketplaceProfileSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        return Response([profile_data(item) for item in available_profiles(self.get_event())])


class TeamOpeningListView(MarketplaceView):
    @extend_schema(responses=TeamOpeningSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        return Response([opening_data(item) for item in available_openings(self.get_event())])

    @extend_schema(request=TeamOpeningInput, responses={201: TeamOpeningSchema})
    def post(self, request, workspace_public_id, event_public_id):
        team = self.captain_membership().team
        serializer = TeamOpeningInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        project_id = data.pop("project", None)
        project = (
            get_object_or_404(Project, team=team, public_id=project_id) if project_id else None
        )
        try:
            data["desired_skills"] = normalize_skills(data["desired_skills"])
            with transaction.atomic():
                opening = TeamOpening(team=team, project=project, **data)
                opening.full_clean()
                opening.save()
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="marketplace.opening_created",
                    target=opening,
                )
        except ModelValidationError as exc:
            raise _validation_error(exc) from exc
        return Response(opening_data(opening), status=201)


class MyTeamOpeningsView(MarketplaceView):
    @extend_schema(responses=TeamOpeningSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        team = self.captain_membership().team
        openings = TeamOpening.objects.filter(team=team).select_related("team", "project")
        return Response([opening_data(item) for item in openings])


class TeamOpeningDetailView(MarketplaceView):
    @extend_schema(request=TeamOpeningInput, responses=TeamOpeningSchema)
    def patch(self, request, workspace_public_id, event_public_id, opening_public_id):
        team = self.captain_membership().team
        serializer = TeamOpeningInput(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            with transaction.atomic():
                opening = get_object_or_404(
                    TeamOpening.objects.select_for_update(of=("self",)),
                    team=team,
                    public_id=opening_public_id,
                )
                if "project" in data:
                    project_id = data.pop("project")
                    opening.project = (
                        get_object_or_404(Project, team=team, public_id=project_id)
                        if project_id
                        else None
                    )
                if "desired_skills" in data:
                    data["desired_skills"] = normalize_skills(data["desired_skills"])
                for key, value in data.items():
                    setattr(opening, key, value)
                opening.full_clean()
                opening.save()
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="marketplace.opening_updated",
                    target=opening,
                )
        except ModelValidationError as exc:
            raise _validation_error(exc) from exc
        return Response(opening_data(opening))


class MarketplaceMatchesView(MarketplaceView):
    @extend_schema(responses=TeamOpeningSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        return Response(matches_for_participant(self.get_event(), request.user))


class OpeningMatchesView(MarketplaceView):
    @extend_schema(responses=MarketplaceProfileSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id, opening_public_id):
        team = self.captain_membership().team
        opening = get_object_or_404(TeamOpening, team=team, public_id=opening_public_id)
        return Response(matches_for_opening(self.get_event(), opening))
