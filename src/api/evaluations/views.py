from accounts.authentication import CookieSessionAuthentication
from accounts.models import User
from audit.services import record_mutation
from core.authz import has_any_role
from core.permissions import require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from events.views import OrganizerView
from projects.models import Project
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from stages.views import StageEventMixin
from workspaces.models import Role

from . import normalization
from .assignment import activate
from .models import (
    Assignment,
    Ballot,
    BallotResponse,
    ConflictOfInterest,
    EvaluationPlan,
    EvaluationPool,
    EvaluationPoolStrategy,
    PoolMembership,
    RubricVersion,
)
from .serializers import (
    AssignmentVersionSerializer,
    BallotSerializer,
    ConflictOfInterestSerializer,
    EvaluationPlanSerializer,
    EvaluationPoolSerializer,
    NormalizationRunSerializer,
    PoolMembershipSerializer,
    RubricVersionSerializer,
)


def _as_drf_validation_error(exc):
    return ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


class PlanMixin(StageEventMixin):
    def get_plan(self):
        return get_object_or_404(
            EvaluationPlan, stage=self.get_stage(), public_id=self.kwargs["plan_public_id"]
        )


class EvaluationPlanListView(StageEventMixin):
    def get(self, request, workspace_public_id, event_public_id, stage_public_id):
        plans = self.get_stage().evaluation_plans.all()
        return Response(EvaluationPlanSerializer(plans, many=True).data)

    def post(self, request, workspace_public_id, event_public_id, stage_public_id):
        serializer = EvaluationPlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            plan = serializer.save(stage=self.get_stage())
            plan.full_clean()
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        except IntegrityError as exc:
            raise ValidationError(
                {"detail": "A plan with this name already exists on this stage."}
            ) from exc
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="evaluation_plan.created",
            target=plan,
        )
        return Response(EvaluationPlanSerializer(plan).data, status=201)


class EvaluationPlanDetailView(PlanMixin):
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        return Response(EvaluationPlanSerializer(self.get_plan()).data)

    def patch(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        serializer = EvaluationPlanSerializer(plan, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            plan = serializer.save()
            plan.full_clean()
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        return Response(EvaluationPlanSerializer(plan).data)

    def delete(
        self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id
    ):
        plan = self.get_plan()
        if plan.rubric_versions.exists():
            raise ValidationError(
                {"detail": "A plan with published rubric versions can't be deleted."}
            )
        plan.delete()
        return Response(status=204)


class RubricPublishView(PlanMixin):
    def post(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        next_number = (plan.current_rubric_version.number + 1) if plan.current_rubric_version else 1
        try:
            with transaction.atomic():
                version = RubricVersion.objects.create(
                    plan=plan, number=next_number, criteria=plan.draft_criteria
                )
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="rubric.published",
            target=version,
        )
        return Response(RubricVersionSerializer(version).data, status=201)


class BallotListCreateView(PlanMixin):
    """Ballot storage (JDG-003): judges submit, organizers audit. A judge
    never sees another judge's ballot -- same isolation invariant as the
    fixture-backed T2 checks elsewhere, now on the real evaluation model.
    """

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        ballots = Ballot.objects.filter(rubric_version__plan=plan).select_related("project")
        if not has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN):
            ballots = ballots.filter(judge=request.user)
        return Response(BallotSerializer(ballots.prefetch_related("responses"), many=True).data)

    def post(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        if not has_any_role(request.user, self.get_workspace(), Role.JUDGE):
            raise ValidationError({"detail": "Only a judge may submit a ballot."})
        plan = self.get_plan()
        version = plan.current_rubric_version
        if version is None:
            raise ValidationError({"detail": "This plan has no published rubric yet."})
        project = get_object_or_404(
            Project, event=self.get_event(), public_id=request.data.get("project")
        )
        if ConflictOfInterest.objects.filter(
            event=self.get_event(), judge=request.user, project=project
        ).exists():
            raise ValidationError({"detail": "You have a declared conflict of interest here."})
        if plan.pool_strategy == EvaluationPoolStrategy.ASSIGNED_SUBSET:
            if (
                plan.active_assignment_version_id is None
                or not Assignment.objects.filter(
                    version_id=plan.active_assignment_version_id,
                    judge=request.user,
                    project=project,
                ).exists()
            ):
                raise ValidationError({"detail": "You are not assigned to evaluate this project."})
        serializer = BallotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        responses = serializer.validated_data.pop("responses")
        try:
            with transaction.atomic():
                ballot = Ballot(
                    rubric_version=version,
                    judge=request.user,
                    project=project,
                    comment=serializer.validated_data.get("comment", ""),
                )
                ballot.full_clean()
                ballot.save()
                for response in responses:
                    entry = BallotResponse(ballot=ballot, **response)
                    entry.full_clean()
                    entry.save()
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        except IntegrityError as exc:
            raise ValidationError(
                {"detail": "You have already submitted a ballot for this project."}
            ) from exc
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="ballot.submitted",
            target=ballot,
        )
        return Response(BallotSerializer(ballot).data, status=201)


class EvaluationPoolListView(OrganizerView):
    def get(self, request, workspace_public_id, event_public_id):
        pools = self.get_event().evaluation_pools.all()
        return Response(EvaluationPoolSerializer(pools, many=True).data)

    def post(self, request, workspace_public_id, event_public_id):
        serializer = EvaluationPoolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            pool = serializer.save(event=self.get_event())
        except IntegrityError as exc:
            raise ValidationError(
                {"detail": "A pool with this name already exists on this event."}
            ) from exc
        return Response(EvaluationPoolSerializer(pool).data, status=201)


class PoolMixin(OrganizerView):
    def get_pool(self):
        return get_object_or_404(
            EvaluationPool, event=self.get_event(), public_id=self.kwargs["pool_public_id"]
        )


class PoolMembershipListView(PoolMixin):
    def get(self, request, workspace_public_id, event_public_id, pool_public_id):
        memberships = self.get_pool().memberships.prefetch_related("track_expertise")
        return Response(PoolMembershipSerializer(memberships, many=True).data)

    def post(self, request, workspace_public_id, event_public_id, pool_public_id):
        pool = self.get_pool()
        judge = get_object_or_404(User, public_id=request.data.get("judge"))
        track_ids = request.data.get("track_expertise", [])
        tracks = pool.event.tracks.filter(public_id__in=track_ids)
        if tracks.count() != len(set(track_ids)):
            raise ValidationError({"track_expertise": "All tracks must belong to this event."})
        membership = PoolMembership(pool=pool, judge=judge)
        try:
            membership.full_clean()
            membership.save()
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        except IntegrityError as exc:
            raise ValidationError(
                {"detail": "This judge is already a member of this pool."}
            ) from exc
        membership.track_expertise.set(tracks)
        return Response(PoolMembershipSerializer(membership).data, status=201)


class PoolMembershipDetailView(PoolMixin):
    def delete(
        self, request, workspace_public_id, event_public_id, pool_public_id, membership_public_id
    ):
        membership = get_object_or_404(
            PoolMembership, pool=self.get_pool(), public_id=membership_public_id
        )
        membership.delete()
        return Response(status=204)


class ConflictOfInterestListCreateView(OrganizerView):
    """Organizer view of all declared conflicts; judges use the same route
    (see permission_classes) but only ever see/create their own -- self-
    declared recusal never requires organizer action to take effect.
    """

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    def get(self, request, workspace_public_id, event_public_id):
        conflicts = ConflictOfInterest.objects.filter(event=self.get_event())
        if not has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN):
            conflicts = conflicts.filter(judge=request.user)
        return Response(ConflictOfInterestSerializer(conflicts, many=True).data)

    def post(self, request, workspace_public_id, event_public_id):
        is_organizer = has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN)
        judge_id = request.data.get("judge")
        judge = (
            get_object_or_404(User, public_id=judge_id)
            if is_organizer and judge_id
            else request.user
        )
        project = get_object_or_404(
            Project, event=self.get_event(), public_id=request.data.get("project")
        )
        conflict = ConflictOfInterest(
            event=self.get_event(),
            judge=judge,
            project=project,
            reason=request.data.get("reason", ""),
            declared_by=request.user,
        )
        try:
            conflict.full_clean()
            conflict.save()
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        except IntegrityError as exc:
            raise ValidationError({"detail": "This conflict is already declared."}) from exc
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="conflict_of_interest.declared",
            target=conflict,
        )
        return Response(ConflictOfInterestSerializer(conflict).data, status=201)


class AssignmentActivateView(PlanMixin):
    def post(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        coverage = request.data.get("coverage", 3)
        if not isinstance(coverage, int) or isinstance(coverage, bool) or coverage < 1:
            raise ValidationError({"coverage": "Must be a positive integer."})
        try:
            with transaction.atomic():
                version = activate(plan, coverage=coverage)
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="assignment.activated",
            target=version,
            metadata=version.evidence,
        )
        return Response(AssignmentVersionSerializer(version).data, status=201)


class AssignmentDetailView(PlanMixin):
    """The active assignment: organizers see everyone's pairing, a judge
    sees only their own (same isolation shape as ballots).
    """

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        if plan.active_assignment_version_id is None:
            return Response(None)
        version = plan.active_assignment_version
        data = AssignmentVersionSerializer(version).data
        if not has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN):
            data["assignments"] = [
                a for a in data["assignments"] if a["judge"] == str(request.user.public_id)
            ]
        return Response(data)


class NormalizationRunListView(PlanMixin):
    """Organizer-only: normalization touches every judge's estimated bias
    at once, which is not something a single judge should be able to
    trigger or needs to see the internals of.
    """

    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        runs = self.get_plan().normalization_runs.all()
        return Response(NormalizationRunSerializer(runs, many=True).data)

    def post(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        ridge_lambda = request.data.get("ridge_lambda", 1.0)
        if (
            not isinstance(ridge_lambda, (int, float))
            or isinstance(ridge_lambda, bool)
            or ridge_lambda < 0
        ):
            raise ValidationError({"ridge_lambda": "Must be a nonnegative number."})
        with transaction.atomic():
            normalization_run = normalization.run(plan, ridge_lambda=ridge_lambda)
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="normalization.run",
            target=normalization_run,
            metadata={"converged": normalization_run.converged, "number": normalization_run.number},
        )
        return Response(NormalizationRunSerializer(normalization_run).data, status=201)
