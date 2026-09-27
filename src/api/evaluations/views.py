import csv
from collections import defaultdict

from accounts.authentication import CookieSessionAuthentication
from accounts.models import User
from audit.services import record_mutation
from core.authz import has_any_role
from core.permissions import IsWorkspaceMember, require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from events.views import OrganizerView
from projects.models import Project
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from stages.views import StageEventMixin
from workspaces.models import Role

from . import normalization, pairwise
from .assignment import activate
from .models import (
    Assignment,
    Ballot,
    BallotDraft,
    BallotResponse,
    ConflictOfInterest,
    EvaluationMode,
    EvaluationPlan,
    EvaluationPool,
    EvaluationPoolStrategy,
    NormalizationRun,
    PairwiseComparison,
    PairwiseRun,
    PoolMembership,
    RubricVersion,
)
from .progress import compute_progress
from .results import pairwise_ranked_results, ranked_results
from .schema import (
    AssignmentActivateInputSchema,
    BallotDraftInputSchema,
    BallotSubmitInputSchema,
    CalibrationProjectItemSchema,
    CalibrationProjectsInputSchema,
    CalibrationProjectSummarySchema,
    CalibrationStatusSchema,
    CandidateQueueItemSchema,
    EvaluationProgressSchema,
    NormalizationInputSchema,
    PairwiseComparisonInputSchema,
    PairwiseNextPairSchema,
    PairwiseRankedResultSchema,
    PairwiseResultsPublishInputSchema,
    PairwiseRunInputSchema,
    PoolMembershipInputSchema,
    RankedResultSchema,
    ResultsPublishInputSchema,
)
from .serializers import (
    AssignmentVersionSerializer,
    BallotDraftSerializer,
    BallotSerializer,
    ConflictOfInterestSerializer,
    EvaluationPlanSerializer,
    EvaluationPoolSerializer,
    NormalizationRunSerializer,
    PairwiseComparisonSerializer,
    PairwiseRunSerializer,
    PoolMembershipSerializer,
    RubricVersionSerializer,
)


def _as_drf_validation_error(exc):
    return ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


def _eligible_candidates(plan, judge):
    """Projects `judge` is expected to evaluate under `plan`'s pool
    strategy, minus their own declared conflicts of interest (JUX-001).
    Shared by the rubric candidate queue and the pairwise next-pair picker
    (S01) so both judging modes draw from exactly the same eligibility rule.
    """
    candidates = Project.objects.filter(
        event_id=plan.stage.event_id, submissions__stage=plan.stage
    ).distinct()
    if plan.pool_strategy == EvaluationPoolStrategy.ASSIGNED_SUBSET:
        if plan.active_assignment_version_id is None:
            return candidates.none()
        candidates = candidates.filter(
            assignments__version_id=plan.active_assignment_version_id,
            assignments__judge=judge,
        )
    conflicted = set(
        ConflictOfInterest.objects.filter(event_id=plan.stage.event_id, judge=judge).values_list(
            "project_id", flat=True
        )
    )
    return candidates.exclude(id__in=conflicted)


def _calibration_remaining(plan, judge):
    """S02: the plan's calibration projects `judge` has not yet scored.
    An empty queryset means calibration is complete (or none is required).
    """
    completed = Ballot.objects.filter(
        rubric_version__plan=plan, judge=judge, is_calibration=True
    ).values_list("project_id", flat=True)
    return plan.calibration_projects.exclude(id__in=completed)


class PlanMixin(StageEventMixin):
    def get_plan(self):
        return get_object_or_404(
            EvaluationPlan, stage=self.get_stage(), public_id=self.kwargs["plan_public_id"]
        )


class EvaluationPlanListView(StageEventMixin):
    serializer_class = EvaluationPlanSerializer

    def get_permissions(self):
        # A judge needs to find the plan(s) that apply to them; only an
        # organizer may create one.
        if self.request.method == "GET":
            return [IsWorkspaceMember()]
        return super().get_permissions()

    def get(self, request, workspace_public_id, event_public_id, stage_public_id):
        plans = self.get_stage().evaluation_plans.all()
        return Response(EvaluationPlanSerializer(plans, many=True).data)

    @extend_schema(responses={201: EvaluationPlanSerializer})
    @transaction.atomic
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
    serializer_class = EvaluationPlanSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsWorkspaceMember()]
        return super().get_permissions()

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
    def get_permissions(self):
        # A judge needs to read the current published rubric to render a
        # ballot form; only an organizer may publish a new version.
        if self.request.method == "GET":
            return [IsWorkspaceMember()]
        return super().get_permissions()

    @extend_schema(responses=RubricVersionSerializer(allow_null=True))
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        version = self.get_plan().current_rubric_version
        if version is None:
            return JsonResponse(None, safe=False)
        return Response(RubricVersionSerializer(version).data)

    @extend_schema(request=None, responses={201: RubricVersionSerializer})
    @transaction.atomic
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

    serializer_class = BallotSerializer

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        """JUX-003: mirrors the official checker's own/peer-score contract
        exactly (integrations.views.JudgeScoresView) -- no `?judge=` means
        "my own scores"; an explicit `?judge=<id>` is refused for anyone but
        that judge themself or an organizer/admin.
        """
        plan = self.get_plan()
        ballots = Ballot.objects.filter(rubric_version__plan=plan).select_related("project")
        is_organizer = has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN)
        requested_judge_id = request.GET.get("judge")
        if requested_judge_id:
            judge = get_object_or_404(User, public_id=requested_judge_id)
            if judge.id != request.user.id and not is_organizer:
                raise PermissionDenied("You cannot view another judge's ballots.")
            ballots = ballots.filter(judge=judge)
        elif not is_organizer:
            ballots = ballots.filter(judge=request.user)
        return Response(BallotSerializer(ballots.prefetch_related("responses"), many=True).data)

    @extend_schema(request=BallotSubmitInputSchema, responses={201: BallotSerializer})
    @transaction.atomic
    def post(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        if not has_any_role(request.user, self.get_workspace(), Role.JUDGE):
            raise ValidationError({"detail": "Only a judge may submit a ballot."})
        plan = self.get_plan()
        if plan.mode != EvaluationMode.RUBRIC:
            raise ValidationError({"detail": "This plan is configured for pairwise judging."})
        if plan.calibration_required and _calibration_remaining(plan, request.user).exists():
            raise ValidationError({"detail": "Complete calibration before live judging."})
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
        BallotDraft.objects.filter(plan=plan, judge=request.user, project=project).delete()
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="ballot.submitted",
            target=ballot,
        )
        return Response(BallotSerializer(ballot).data, status=201)


class BallotDraftView(PlanMixin):
    """Autosave storage for an in-progress ballot (JUX-002): a judge can
    save partial/invalid state freely here without ever touching the
    immutable submitted-evidence tables. Submitting goes through
    BallotListCreateView.post, which deletes the matching draft on success.
    """

    serializer_class = BallotDraftSerializer

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.JUDGE)]

    def get_project(self):
        return get_object_or_404(
            Project, event=self.get_event(), public_id=self.kwargs["project_public_id"]
        )

    @extend_schema(responses=BallotDraftSerializer(allow_null=True))
    def get(
        self,
        request,
        workspace_public_id,
        event_public_id,
        stage_public_id,
        plan_public_id,
        project_public_id,
    ):
        draft = BallotDraft.objects.filter(
            plan=self.get_plan(), judge=request.user, project=self.get_project()
        ).first()
        if draft is None:
            # A bare DRF `Response(None)` renders to an empty body with no
            # Content-Type (DRF treats None as "no content"), which breaks
            # any client expecting a parseable `null` -- use JsonResponse
            # instead so this actually round-trips.
            return JsonResponse(None, safe=False)
        return Response(BallotDraftSerializer(draft).data)

    @extend_schema(request=BallotDraftInputSchema, responses=BallotDraftSerializer)
    def put(
        self,
        request,
        workspace_public_id,
        event_public_id,
        stage_public_id,
        plan_public_id,
        project_public_id,
    ):
        plan = self.get_plan()
        project = self.get_project()
        responses = request.data.get("responses", {})
        if not isinstance(responses, dict):
            raise ValidationError({"responses": "Must be an object of criterion_id -> score."})
        draft, _ = BallotDraft.objects.update_or_create(
            plan=plan,
            judge=request.user,
            project=project,
            defaults={"responses": responses, "comment": request.data.get("comment", "")},
        )
        return Response(BallotDraftSerializer(draft).data)

    def delete(
        self,
        request,
        workspace_public_id,
        event_public_id,
        stage_public_id,
        plan_public_id,
        project_public_id,
    ):
        BallotDraft.objects.filter(
            plan=self.get_plan(), judge=request.user, project=self.get_project()
        ).delete()
        return Response(status=204)


class EvaluationPoolListView(OrganizerView):
    serializer_class = EvaluationPoolSerializer

    def get(self, request, workspace_public_id, event_public_id):
        pools = self.get_event().evaluation_pools.all()
        return Response(EvaluationPoolSerializer(pools, many=True).data)

    @extend_schema(responses={201: EvaluationPoolSerializer})
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
    serializer_class = PoolMembershipSerializer

    def get(self, request, workspace_public_id, event_public_id, pool_public_id):
        memberships = self.get_pool().memberships.prefetch_related("track_expertise")
        return Response(PoolMembershipSerializer(memberships, many=True).data)

    @extend_schema(request=PoolMembershipInputSchema, responses={201: PoolMembershipSerializer})
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
    @extend_schema(responses={204: None})
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

    serializer_class = ConflictOfInterestSerializer

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    def get(self, request, workspace_public_id, event_public_id):
        conflicts = ConflictOfInterest.objects.filter(event=self.get_event())
        if not has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN):
            conflicts = conflicts.filter(judge=request.user)
        return Response(ConflictOfInterestSerializer(conflicts, many=True).data)

    @extend_schema(responses={201: ConflictOfInterestSerializer})
    @transaction.atomic
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
    @extend_schema(
        request=AssignmentActivateInputSchema, responses={201: AssignmentVersionSerializer}
    )
    @transaction.atomic
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

    serializer_class = AssignmentVersionSerializer

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        if plan.active_assignment_version_id is None:
            # See BallotDraftView.get for why this isn't a bare Response(None).
            return JsonResponse(None, safe=False)
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

    serializer_class = NormalizationRunSerializer

    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        runs = self.get_plan().normalization_runs.all()
        return Response(NormalizationRunSerializer(runs, many=True).data)

    @extend_schema(request=NormalizationInputSchema, responses={201: NormalizationRunSerializer})
    @transaction.atomic
    def post(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        if plan.mode != EvaluationMode.RUBRIC:
            raise ValidationError({"detail": "This plan is configured for pairwise judging."})
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


class EvaluationProgressView(PlanMixin):
    """JUX-004: coverage/load/completion/normalization state in one call."""

    @extend_schema(responses=EvaluationProgressSchema)
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        return Response(compute_progress(self.get_plan()))


class ResultsPublishView(PlanMixin):
    """JUX-005: point a plan at the normalization run its results are drawn
    from, with any organizer tie-break overrides. Publishing is what makes
    results reachable at all (ResultsView 404s until this has run once).
    """

    @extend_schema(request=ResultsPublishInputSchema, responses=EvaluationPlanSerializer)
    @transaction.atomic
    def post(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        run = get_object_or_404(
            NormalizationRun, plan=plan, public_id=request.data.get("normalization_run")
        )
        tie_breaks = request.data.get("tie_breaks", {})
        if not isinstance(tie_breaks, dict) or not all(
            isinstance(v, int) and not isinstance(v, bool) for v in tie_breaks.values()
        ):
            raise ValidationError({"tie_breaks": "Must map project public_id to an integer."})
        resolved = {}
        for project_public_id, value in tie_breaks.items():
            project = get_object_or_404(
                Project, event=self.get_event(), public_id=project_public_id
            )
            resolved[str(project.id)] = value
        plan.published_normalization_run = run
        plan.tie_breaks = resolved
        plan.full_clean()
        plan.save(update_fields=["published_normalization_run", "tie_breaks", "updated_at"])
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="results.published",
            target=plan,
            metadata={"normalization_run": run.number},
        )
        return Response(EvaluationPlanSerializer(plan).data)


def _serialize_ranked(result, projects_by_id):
    project = projects_by_id.get(result.project_id)
    return {
        "rank": result.rank,
        "project": str(project.public_id) if project else None,
        "project_name": project.name if project else None,
        "raw_score": result.raw_score,
        "final_score": result.final_score,
        "tie_break": result.tie_break,
    }


class ResultsView(PlanMixin):
    """Public-ish read of published results: organizers/admins always see
    them; anyone else (participants) only once the organizer has both
    published a run AND opted into `results_visible_to_participants`.
    """

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.PARTICIPANT, Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(responses=RankedResultSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        is_organizer = has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN)
        if plan.published_normalization_run_id is None:
            return Response(status=404)
        if not is_organizer and not plan.results_visible_to_participants:
            raise PermissionDenied("Results are not yet visible to participants.")
        results = ranked_results(plan, plan.published_normalization_run)
        projects_by_id = {
            p.id: p for p in Project.objects.filter(id__in=[r.project_id for r in results])
        }
        return Response([_serialize_ranked(r, projects_by_id) for r in results])


class ResultsCsvExportView(PlanMixin):
    """JUX-006: organizer CSV export of a plan's published results."""

    @extend_schema(responses={(200, "text/csv"): OpenApiTypes.BINARY})
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        if plan.published_normalization_run_id is None:
            return Response({"detail": "No results have been published for this plan."}, status=404)
        results = ranked_results(plan, plan.published_normalization_run)
        projects_by_id = {
            p.id: p for p in Project.objects.filter(id__in=[r.project_id for r in results])
        }

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="results.csv"'
        writer = csv.writer(response)
        writer.writerow(["rank", "project", "raw_score", "final_score", "tie_break"])
        for result in results:
            project = projects_by_id.get(result.project_id)
            writer.writerow(
                [
                    result.rank,
                    project.name if project else result.project_id,
                    result.raw_score,
                    result.final_score,
                    result.tie_break if result.tie_break is not None else "",
                ]
            )
        return response


class CandidateListView(PlanMixin):
    """JUX-001: the judge's own queue -- every candidate they're expected to
    review under this plan's strategy, minus their own declared conflicts,
    each flagged with where they've gotten to (pending/drafted/submitted).
    """

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(responses=CandidateQueueItemSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        if not has_any_role(request.user, self.get_workspace(), Role.JUDGE):
            raise ValidationError({"detail": "Only a judge has a review queue."})

        candidates = _eligible_candidates(plan, request.user).order_by("name")

        submitted = set(
            Ballot.objects.filter(rubric_version__plan=plan, judge=request.user).values_list(
                "project_id", flat=True
            )
        )
        drafted = set(
            BallotDraft.objects.filter(plan=plan, judge=request.user).values_list(
                "project_id", flat=True
            )
        )
        return Response(
            [
                {
                    "project": str(project.public_id),
                    "name": project.name,
                    "status": (
                        "submitted"
                        if project.id in submitted
                        else "drafted"
                        if project.id in drafted
                        else "pending"
                    ),
                }
                for project in candidates
            ]
        )


class PairwiseNextPairView(PlanMixin):
    """S01: the next pair of candidates for the requesting judge to compare
    under a PAIRWISE-mode plan -- the two eligible, not-yet-compared-by-
    this-judge candidates with the fewest comparisons so far, so coverage
    balances across the field instead of a judge repeatedly seeing the
    same popular pair. Returns null once every eligible pair has been
    judged (or fewer than two eligible candidates exist).
    """

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(responses=PairwiseNextPairSchema(allow_null=True))
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        if plan.mode != EvaluationMode.PAIRWISE:
            raise ValidationError({"detail": "This plan is not configured for pairwise judging."})
        if not has_any_role(request.user, self.get_workspace(), Role.JUDGE):
            raise ValidationError({"detail": "Only a judge has a comparison queue."})

        candidate_ids = list(
            _eligible_candidates(plan, request.user).order_by("id").values_list("id", flat=True)
        )
        already_compared = set(
            PairwiseComparison.objects.filter(plan=plan, judge=request.user).values_list(
                "project_a_id", "project_b_id"
            )
        )
        comparison_counts = defaultdict(int)
        for a, b in PairwiseComparison.objects.filter(
            plan=plan, project_a_id__in=candidate_ids, project_b_id__in=candidate_ids
        ).values_list("project_a_id", "project_b_id"):
            comparison_counts[a] += 1
            comparison_counts[b] += 1

        best_pair = None
        best_load = None
        for index, project_a_id in enumerate(candidate_ids):
            for project_b_id in candidate_ids[index + 1 :]:
                if (project_a_id, project_b_id) in already_compared:
                    continue
                load = comparison_counts[project_a_id] + comparison_counts[project_b_id]
                if best_load is None or load < best_load:
                    best_load = load
                    best_pair = (project_a_id, project_b_id)

        if best_pair is None:
            # See BallotDraftView.get for why this isn't a bare Response(None).
            return JsonResponse(None, safe=False)
        projects = {p.id: p for p in Project.objects.filter(id__in=best_pair)}
        return Response(
            {
                "project_a": str(projects[best_pair[0]].public_id),
                "project_b": str(projects[best_pair[1]].public_id),
            }
        )


class PairwiseComparisonListCreateView(PlanMixin):
    """Pairwise comparison storage (S01): a judge submits a head-to-head
    verdict; isolation mirrors BallotListCreateView -- a judge never sees
    another judge's comparisons unless they organize.
    """

    serializer_class = PairwiseComparisonSerializer

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        comparisons = PairwiseComparison.objects.filter(plan=plan).select_related(
            "judge", "project_a", "project_b", "winner"
        )
        is_organizer = has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN)
        requested_judge_id = request.GET.get("judge")
        if requested_judge_id:
            judge = get_object_or_404(User, public_id=requested_judge_id)
            if judge.id != request.user.id and not is_organizer:
                raise PermissionDenied("You cannot view another judge's comparisons.")
            comparisons = comparisons.filter(judge=judge)
        elif not is_organizer:
            comparisons = comparisons.filter(judge=request.user)
        return Response(PairwiseComparisonSerializer(comparisons, many=True).data)

    @extend_schema(
        request=PairwiseComparisonInputSchema, responses={201: PairwiseComparisonSerializer}
    )
    @transaction.atomic
    def post(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        if not has_any_role(request.user, self.get_workspace(), Role.JUDGE):
            raise ValidationError({"detail": "Only a judge may submit a comparison."})
        plan = self.get_plan()
        if plan.mode != EvaluationMode.PAIRWISE:
            raise ValidationError({"detail": "This plan is not configured for pairwise judging."})
        event = self.get_event()
        project_a = get_object_or_404(Project, event=event, public_id=request.data.get("project_a"))
        project_b = get_object_or_404(Project, event=event, public_id=request.data.get("project_b"))
        winner = None
        winner_public_id = request.data.get("winner")
        if winner_public_id:
            winner = get_object_or_404(Project, event=event, public_id=winner_public_id)

        if ConflictOfInterest.objects.filter(
            event=event, judge=request.user, project__in=[project_a, project_b]
        ).exists():
            raise ValidationError({"detail": "You have a declared conflict of interest here."})
        eligible_ids = set(_eligible_candidates(plan, request.user).values_list("id", flat=True))
        if project_a.id not in eligible_ids or project_b.id not in eligible_ids:
            raise ValidationError(
                {"detail": "You are not assigned to compare one of these projects."}
            )

        comparison = PairwiseComparison(
            plan=plan, judge=request.user, project_a=project_a, project_b=project_b, winner=winner
        )
        try:
            with transaction.atomic():
                comparison.full_clean()
                comparison.save()
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        except IntegrityError as exc:
            raise ValidationError(
                {"detail": "You have already compared these two candidates."}
            ) from exc
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="pairwise_comparison.submitted",
            target=comparison,
        )
        return Response(PairwiseComparisonSerializer(comparison).data, status=201)


class PairwiseRunListView(PlanMixin):
    """Organizer-only: mirrors NormalizationRunListView but computes
    Bradley-Terry strengths for a PAIRWISE-mode plan's comparisons (S01).
    """

    serializer_class = PairwiseRunSerializer

    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        runs = self.get_plan().pairwise_runs.all()
        return Response(PairwiseRunSerializer(runs, many=True).data)

    @extend_schema(request=PairwiseRunInputSchema, responses={201: PairwiseRunSerializer})
    @transaction.atomic
    def post(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        if plan.mode != EvaluationMode.PAIRWISE:
            raise ValidationError({"detail": "This plan is not configured for pairwise judging."})
        prior_games = request.data.get("prior_games", 2.0)
        if (
            not isinstance(prior_games, (int, float))
            or isinstance(prior_games, bool)
            or prior_games < 0
        ):
            raise ValidationError({"prior_games": "Must be a nonnegative number."})
        with transaction.atomic():
            pairwise_run = pairwise.run(plan, prior_games=prior_games)
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="pairwise_run.computed",
            target=pairwise_run,
            metadata={"converged": pairwise_run.converged, "number": pairwise_run.number},
        )
        return Response(PairwiseRunSerializer(pairwise_run).data, status=201)


class PairwiseResultsPublishView(PlanMixin):
    """S01: pairwise analogue of ResultsPublishView -- points a plan at the
    PairwiseRun its published ranking is drawn from.
    """

    @extend_schema(request=PairwiseResultsPublishInputSchema, responses=EvaluationPlanSerializer)
    @transaction.atomic
    def post(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        run = get_object_or_404(PairwiseRun, plan=plan, public_id=request.data.get("pairwise_run"))
        tie_breaks = request.data.get("tie_breaks", {})
        if not isinstance(tie_breaks, dict) or not all(
            isinstance(v, int) and not isinstance(v, bool) for v in tie_breaks.values()
        ):
            raise ValidationError({"tie_breaks": "Must map project public_id to an integer."})
        resolved = {}
        for project_public_id, value in tie_breaks.items():
            project = get_object_or_404(
                Project, event=self.get_event(), public_id=project_public_id
            )
            resolved[str(project.id)] = value
        plan.published_pairwise_run = run
        plan.tie_breaks = resolved
        plan.full_clean()
        plan.save(update_fields=["published_pairwise_run", "tie_breaks", "updated_at"])
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="pairwise_results.published",
            target=plan,
            metadata={"pairwise_run": run.number},
        )
        return Response(EvaluationPlanSerializer(plan).data)


def _serialize_pairwise_ranked(result, projects_by_id):
    project = projects_by_id.get(result.project_id)
    return {
        "rank": result.rank,
        "project": str(project.public_id) if project else None,
        "project_name": project.name if project else None,
        "strength": result.strength,
        "win_count": result.win_count,
        "comparison_count": result.comparison_count,
        "tie_break": result.tie_break,
    }


class PairwiseResultsView(PlanMixin):
    """S01: pairwise analogue of ResultsView, same visibility rule."""

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.PARTICIPANT, Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(responses=PairwiseRankedResultSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        is_organizer = has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN)
        if plan.published_pairwise_run_id is None:
            return Response(status=404)
        if not is_organizer and not plan.results_visible_to_participants:
            raise PermissionDenied("Results are not yet visible to participants.")
        results = pairwise_ranked_results(plan, plan.published_pairwise_run)
        projects_by_id = {
            p.id: p for p in Project.objects.filter(id__in=[r.project_id for r in results])
        }
        return Response([_serialize_pairwise_ranked(r, projects_by_id) for r in results])


class PairwiseResultsCsvExportView(PlanMixin):
    """S01: pairwise analogue of ResultsCsvExportView."""

    @extend_schema(responses={(200, "text/csv"): OpenApiTypes.BINARY})
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        if plan.published_pairwise_run_id is None:
            return Response({"detail": "No results have been published for this plan."}, status=404)
        results = pairwise_ranked_results(plan, plan.published_pairwise_run)
        projects_by_id = {
            p.id: p for p in Project.objects.filter(id__in=[r.project_id for r in results])
        }

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="pairwise-results.csv"'
        writer = csv.writer(response)
        writer.writerow(
            ["rank", "project", "strength", "win_count", "comparison_count", "tie_break"]
        )
        for result in results:
            project = projects_by_id.get(result.project_id)
            writer.writerow(
                [
                    result.rank,
                    project.name if project else result.project_id,
                    result.strength,
                    result.win_count,
                    result.comparison_count,
                    result.tie_break if result.tie_break is not None else "",
                ]
            )
        return response


class CalibrationProjectsView(PlanMixin):
    """S02: the plan's shared calibration project set -- every judge scores
    these against the rubric's anchors before live judging (when
    `calibration_required` is set). A judge needs the list to know what to
    score; only an organizer may change it.
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [require_roles(Role.JUDGE, Role.ORGANIZER, Role.ADMIN)()]
        return super().get_permissions()

    @extend_schema(responses=CalibrationProjectItemSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        projects = self.get_plan().calibration_projects.all()
        return Response([{"project": str(p.public_id), "name": p.name} for p in projects])

    @extend_schema(
        request=CalibrationProjectsInputSchema, responses=CalibrationProjectItemSchema(many=True)
    )
    def put(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        event = self.get_event()
        project_ids = request.data.get("projects", [])
        if not isinstance(project_ids, list):
            raise ValidationError({"projects": "Must be a list of project ids."})
        projects = list(Project.objects.filter(event=event, public_id__in=project_ids))
        if len(projects) != len(set(project_ids)):
            raise ValidationError({"projects": "All projects must belong to this event."})
        plan.calibration_projects.set(projects)
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="calibration_projects.set",
            target=plan,
            metadata={"count": len(projects)},
        )
        return Response([{"project": str(p.public_id), "name": p.name} for p in projects])


class CalibrationBallotListCreateView(PlanMixin):
    """S02: a judge's calibration ballot on one of the plan's shared
    calibration projects -- separate evidence from live Ballots (see
    Ballot.is_calibration and scoring.ballot_observations), same isolation
    shape as BallotListCreateView.
    """

    serializer_class = BallotSerializer

    def get_permissions(self):
        return [require_roles(Role.JUDGE, Role.ORGANIZER, Role.ADMIN)()]

    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        ballots = Ballot.objects.filter(
            rubric_version__plan=plan, is_calibration=True
        ).select_related("project")
        is_organizer = has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN)
        requested_judge_id = request.GET.get("judge")
        if requested_judge_id:
            judge = get_object_or_404(User, public_id=requested_judge_id)
            if judge.id != request.user.id and not is_organizer:
                raise PermissionDenied("You cannot view another judge's calibration ballots.")
            ballots = ballots.filter(judge=judge)
        elif not is_organizer:
            ballots = ballots.filter(judge=request.user)
        return Response(BallotSerializer(ballots.prefetch_related("responses"), many=True).data)

    @extend_schema(request=BallotSubmitInputSchema, responses={201: BallotSerializer})
    @transaction.atomic
    def post(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        if not has_any_role(request.user, self.get_workspace(), Role.JUDGE):
            raise ValidationError({"detail": "Only a judge may submit a calibration ballot."})
        plan = self.get_plan()
        version = plan.current_rubric_version
        if version is None:
            raise ValidationError({"detail": "This plan has no published rubric yet."})
        project = get_object_or_404(
            Project, event=self.get_event(), public_id=request.data.get("project")
        )
        if not plan.calibration_projects.filter(id=project.id).exists():
            raise ValidationError({"detail": "Not one of this plan's calibration projects."})
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
                    is_calibration=True,
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
                {"detail": "You have already submitted a calibration ballot for this project."}
            ) from exc
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="calibration_ballot.submitted",
            target=ballot,
        )
        return Response(BallotSerializer(ballot).data, status=201)


class CalibrationStatusView(PlanMixin):
    """S02: a judge's own calibration completion status; an organizer may
    check any specific judge via `?judge=`, same pattern as the ballot and
    pairwise-comparison list views.
    """

    def get_permissions(self):
        return [require_roles(Role.JUDGE, Role.ORGANIZER, Role.ADMIN)()]

    @extend_schema(responses=CalibrationStatusSchema)
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        is_organizer = has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN)
        requested_judge_id = request.GET.get("judge")
        if requested_judge_id:
            judge = get_object_or_404(User, public_id=requested_judge_id)
            if judge.id != request.user.id and not is_organizer:
                raise PermissionDenied("You cannot view another judge's calibration status.")
        elif has_any_role(request.user, self.get_workspace(), Role.JUDGE):
            judge = request.user
        else:
            raise ValidationError({"detail": "Specify ?judge= or use a judge session."})

        remaining_ids = set(_calibration_remaining(plan, judge).values_list("id", flat=True))
        all_projects = list(plan.calibration_projects.values_list("id", "public_id"))
        completed = [str(public_id) for pk, public_id in all_projects if pk not in remaining_ids]
        remaining = [str(public_id) for pk, public_id in all_projects if pk in remaining_ids]
        return Response(
            {
                "required": plan.calibration_required,
                "total": len(all_projects),
                "completed": completed,
                "remaining": remaining,
                "is_complete": not remaining,
            }
        )


class CalibrationSummaryView(PlanMixin):
    """S02: organizer-only raw per-criterion calibration scores across
    judges for each calibration project -- evidence to review rubric
    anchors before opening live judging. Deliberately just raw scores plus
    min/max/mean/spread, not a formal inter-rater agreement statistic (see
    JUDGING.md; S03 covers proper agreement analytics).
    """

    @extend_schema(responses=CalibrationProjectSummarySchema(many=True))
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        ballots = (
            Ballot.objects.filter(rubric_version__plan=plan, is_calibration=True)
            .select_related("judge")
            .prefetch_related("responses")
        )
        by_project = defaultdict(list)
        for ballot in ballots:
            by_project[ballot.project_id].append(ballot)

        summaries = []
        for project in plan.calibration_projects.all():
            by_criterion = defaultdict(dict)
            for ballot in by_project.get(project.id, []):
                judge_label = str(ballot.judge.public_id)
                for response in ballot.responses.all():
                    by_criterion[response.criterion_id][judge_label] = response.score
            criteria = [
                {
                    "criterion_id": criterion_id,
                    "scores": scores,
                    "min": min(scores.values()),
                    "max": max(scores.values()),
                    "mean": sum(scores.values()) / len(scores),
                    "spread": max(scores.values()) - min(scores.values()),
                }
                for criterion_id, scores in sorted(by_criterion.items())
            ]
            summaries.append(
                {
                    "project": str(project.public_id),
                    "project_name": project.name,
                    "criteria": criteria,
                }
            )
        return Response(summaries)
