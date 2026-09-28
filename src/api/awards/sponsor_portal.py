"""VS19: sponsor portal -- read access to prize definitions, eligible
projects and assigned judges, plus the same fulfillment state machine
organizers use, all scoped to the awards a sponsor is actually tagged on
(see `Award.sponsor_contacts`, VS18/VS19). Reuses the exact organizer
helpers/service in `.views`/`.services` rather than a parallel read path,
so a rule change there can never silently drift from what a sponsor sees.
"""

from core.authz import has_any_role
from core.permissions import require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from evaluations.models import PoolMembership
from events.views import OrganizerView
from projects.models import Project, SubmissionStatus
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from workspaces.models import Role

from .models import Award, AwardResource, PrizeFulfillment
from .services import advance_fulfillment
from .views import (
    FulfillmentInput,
    FulfillmentOutput,
    ResourceInput,
    ResourceOutput,
    _resource_data,
    award_data,
    fulfillment_data,
)


class SponsorPortalBase(OrganizerView):
    permission_classes = [require_roles(Role.SPONSOR, Role.ORGANIZER, Role.ADMIN)]

    def is_organizer(self, request):
        return has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN)

    def get_award(self, award_public_id):
        return get_object_or_404(Award, event=self.get_event(), public_id=award_public_id)

    def ensure_can_manage(self, request, award):
        if (
            not self.is_organizer(request)
            and not award.sponsor_contacts.filter(pk=request.user.pk).exists()
        ):
            raise PermissionDenied("You are not a sponsor contact for this award.")


def _eligible_projects(award):
    projects = Project.objects.filter(event=award.event)
    if award.eligibility_track_id:
        projects = projects.filter(track_id=award.eligibility_track_id)
    if award.require_finalized_submission:
        projects = projects.filter(submissions__status=SubmissionStatus.FINALIZED).distinct()
    return projects


def _award_judges(award):
    if not award.evaluation_plan_id or not award.evaluation_plan.pool_id:
        return []
    memberships = PoolMembership.objects.filter(
        pool_id=award.evaluation_plan.pool_id
    ).select_related("judge")
    return sorted({membership.judge.username for membership in memberships})


def _sponsor_award_data(award):
    data = award_data(award)
    data["eligible_projects"] = [
        {"public_id": str(project.public_id), "name": project.name}
        for project in _eligible_projects(award).order_by("name", "pk")
    ]
    data["judges"] = _award_judges(award)
    return data


class SponsorPortalAwardListView(SponsorPortalBase):
    @extend_schema(responses=None)
    def get(self, request, workspace_public_id, event_public_id):
        awards = Award.objects.filter(event=self.get_event())
        if not self.is_organizer(request):
            awards = awards.filter(sponsor_contacts=request.user)
        return Response([_sponsor_award_data(award) for award in awards.distinct().order_by("pk")])


class SponsorPortalFulfillmentView(SponsorPortalBase):
    @extend_schema(request=FulfillmentInput, responses=FulfillmentOutput)
    def patch(self, request, workspace_public_id, event_public_id, fulfillment_public_id):
        fulfillment = get_object_or_404(
            PrizeFulfillment,
            public_id=fulfillment_public_id,
            winner__award__event=self.get_event(),
        )
        self.ensure_can_manage(request, fulfillment.winner.award)
        data = FulfillmentInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            updated = advance_fulfillment(
                fulfillment=fulfillment,
                target=data.validated_data["state"],
                actor=request.user,
                note=data.validated_data.get("note", ""),
            )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(fulfillment_data(updated))


class SponsorPortalResourceListView(SponsorPortalBase):
    """PVS09: challenge content (API docs, starter repos, contacts, FAQ,
    workshop references) an award's sponsor -- or an organizer -- manages
    for that award.
    """

    @extend_schema(request=ResourceInput, responses={201: ResourceOutput})
    def post(self, request, workspace_public_id, event_public_id, award_public_id):
        award = self.get_award(award_public_id)
        self.ensure_can_manage(request, award)
        data = ResourceInput(data=request.data)
        data.is_valid(raise_exception=True)
        resource = AwardResource(award=award, created_by=request.user, **data.validated_data)
        try:
            resource.full_clean()
            resource.save()
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(_resource_data(resource), status=201)


class SponsorPortalResourceDetailView(SponsorPortalBase):
    def get_resource(self, award, resource_public_id):
        return get_object_or_404(AwardResource, award=award, public_id=resource_public_id)

    @extend_schema(request=ResourceInput, responses=ResourceOutput)
    def patch(
        self, request, workspace_public_id, event_public_id, award_public_id, resource_public_id
    ):
        award = self.get_award(award_public_id)
        self.ensure_can_manage(request, award)
        resource = self.get_resource(award, resource_public_id)
        data = ResourceInput(data=request.data, partial=True)
        data.is_valid(raise_exception=True)
        for field, value in data.validated_data.items():
            setattr(resource, field, value)
        try:
            resource.full_clean()
            resource.save()
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(_resource_data(resource))

    @extend_schema(responses={204: None})
    def delete(
        self, request, workspace_public_id, event_public_id, award_public_id, resource_public_id
    ):
        award = self.get_award(award_public_id)
        self.ensure_can_manage(request, award)
        self.get_resource(award, resource_public_id).delete()
        return Response(status=204)
