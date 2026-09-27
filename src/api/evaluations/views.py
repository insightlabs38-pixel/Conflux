import csv
import math
from collections import defaultdict

from accounts.authentication import CookieSessionAuthentication
from accounts.models import User
from audit.services import diff_snapshots, record_mutation
from awards.models import AwardWinner, SelectionSource
from core.authz import has_any_role
from core.permissions import IsWorkspaceMember, require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, inline_serializer
from events.views import OrganizerView
from participation.models import Team
from projects.models import Project
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from stages.serializers import StageSerializer
from stages.views import StageEventMixin
from workspaces.models import Role

from . import agreement, anonymize, normalization, pairwise
from .assignment import activate, rebalance, simulate_dropout
from .assignment import preview as preview_assignment
from .coi import conflict_pairs, is_conflicted
from .eligibility import eligible_projects
from .hybrid import close_call_project_ids
from .models import (
    Assignment,
    Ballot,
    BallotDraft,
    BallotResponse,
    COIRule,
    COIRuleKind,
    ConflictOfInterest,
    EvaluationMode,
    EvaluationPlan,
    EvaluationPool,
    EvaluationPoolStrategy,
    JudgeCOIRelationship,
    NormalizationRun,
    PairwiseComparison,
    PairwiseRun,
    PoolMembership,
    ProjectCOIAttribute,
    RubricVersion,
)
from .optimization import activate_optimized
from .optimization import compare as compare_assignments
from .progress import compute_progress
from .results import pairwise_ranked_results, ranked_results
from .schema import (
    AgreementSummarySchema,
    AssignmentActivateInputSchema,
    AssignmentCompareInputSchema,
    AssignmentCompareSchema,
    AssignmentCoveragePreviewSchema,
    AssignmentPreviewInputSchema,
    AssignmentRebalanceInputSchema,
    BallotDraftInputSchema,
    BallotSubmitInputSchema,
    CalibrationProjectItemSchema,
    CalibrationProjectsInputSchema,
    CalibrationProjectSummarySchema,
    CalibrationStatusSchema,
    CandidateQueueItemSchema,
    CloseCallsSchema,
    COIRuleInputSchema,
    COIRuleOutputSchema,
    DropoutSimulationInputSchema,
    DropoutSimulationSchema,
    EvaluationProgressSchema,
    FeedbackEntrySchema,
    JudgeCalendarSchema,
    JudgeCOIRelationshipInputSchema,
    JudgeWorkloadRowSchema,
    NormalizationInputSchema,
    PairwiseComparisonInputSchema,
    PairwiseNextPairSchema,
    PairwiseRankedResultSchema,
    PairwiseResultsPublishInputSchema,
    PairwiseRunInputSchema,
    PoolMembershipInputSchema,
    ProjectCOIAttributeInputSchema,
    ProvenanceSchema,
    RankedResultSchema,
    ResultsPublishInputSchema,
    SensitivityInputSchema,
)
from .sensitivity import (
    DEFAULT_HOLDOUT_COUNTS,
    DEFAULT_RIDGE_LAMBDAS,
    chronological_observations,
    incompleteness_sensitivity,
    judge_removal_sensitivity,
    ridge_lambda_sensitivity,
)
from .serializers import (
    AssignmentVersionSerializer,
    BallotDraftSerializer,
    BallotSerializer,
    ConflictOfInterestSerializer,
    EvaluationPlanSerializer,
    EvaluationPoolSerializer,
    JudgeCOIRelationshipSerializer,
    NormalizationRunSerializer,
    PairwiseComparisonSerializer,
    PairwiseRunSerializer,
    PoolMembershipSerializer,
    ProjectCOIAttributeSerializer,
    RubricVersionSerializer,
)
from .workflow_presets import PRESETS as WORKFLOW_PRESETS
from .workflow_presets import apply_preset


def _as_drf_validation_error(exc):
    return ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


def _eligible_candidates(plan, judge):
    """Projects `judge` is expected to evaluate under `plan`'s pool
    strategy, minus their own declared conflicts of interest (JUX-001).
    Shared by the rubric candidate queue and the pairwise next-pair picker
    (S01) so both judging modes draw from exactly the same eligibility rule.
    """
    candidates = eligible_projects(plan)
    if (
        plan.prize_judging
        and not PoolMembership.objects.filter(pool_id=plan.pool_id, judge=judge).exists()
    ):
        return candidates.none()
    if plan.pool_strategy == EvaluationPoolStrategy.ASSIGNED_SUBSET:
        if plan.active_assignment_version_id is None:
            return candidates.none()
        candidates = candidates.filter(
            assignments__version_id=plan.active_assignment_version_id,
            assignments__judge=judge,
        )
    conflicted = {
        project_id for _, project_id in conflict_pairs(plan.stage.event_id, judge_ids={judge.id})
    }
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


class WorkflowPresetListView(OrganizerView):
    @extend_schema(
        responses={
            200: {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "rounds": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["label", "rounds"],
                },
            }
        }
    )
    def get(self, request, workspace_public_id, event_public_id):
        return Response(
            {
                slug: {"label": preset["label"], "rounds": preset["rounds"]}
                for slug, preset in WORKFLOW_PRESETS.items()
            }
        )


class WorkflowPresetApplyView(OrganizerView):
    """Bootstraps a fresh event's stage graph from a named multi-round
    preset (S20) -- a one-action shortcut for what an organizer could
    already build stage by stage through StageListView/StageTransitionList
    View/EvaluationPlanListView.
    """

    @extend_schema(
        request=inline_serializer(
            "WorkflowPresetInput", fields={"preset": serializers.CharField()}
        ),
        responses={
            201: inline_serializer(
                "WorkflowPresetResult",
                fields={
                    "stages": StageSerializer(many=True),
                    "plans": EvaluationPlanSerializer(many=True),
                },
            )
        },
    )
    @transaction.atomic
    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        preset_slug = request.data.get("preset", "")
        try:
            stages, plans = apply_preset(event, preset_slug)
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="workflow_preset.applied",
            target=event,
            event_type="workflow_preset.applied",
            payload={"event": str(event.public_id), "preset": preset_slug},
            metadata={
                "event_id": str(event.public_id),
                "preset": preset_slug,
                "stages": [str(stage.public_id) for stage in stages],
            },
        )
        return Response(
            {
                "stages": StageSerializer(stages, many=True).data,
                "plans": EvaluationPlanSerializer(plans, many=True).data,
            },
            status=201,
        )


class JudgeCalendarView(OrganizerView):
    """S24: one judge's own time-aware view across every plan in the
    event -- this event's open/closed windows (`TemporalGate`s aren't
    tied to a specific plan in the data model, so they're reported
    alongside assignments rather than invented as a per-plan link) plus
    their assigned/submitted count per plan they actually have candidates
    in. Reuses `_eligible_candidates` so eligibility (pool strategy,
    conflicts, prize-pool membership) is exactly what judging itself uses.
    """

    permission_classes = [require_roles(Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(responses=JudgeCalendarSchema)
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        windows = [
            {
                "name": gate.name,
                "opens_at": gate.opens_at,
                "closes_at": gate.closes_at,
                "status": gate.status(),
            }
            for gate in event.temporal_gates.all()
        ]
        assignments = []
        for plan in EvaluationPlan.objects.filter(stage__event=event).select_related("stage"):
            assigned = _eligible_candidates(plan, request.user).count()
            if assigned == 0:
                continue
            submitted = Ballot.objects.filter(
                rubric_version__plan=plan, judge=request.user, is_calibration=False
            ).count()
            assignments.append(
                {
                    "stage_name": plan.stage.name,
                    "plan": str(plan.public_id),
                    "plan_name": plan.name,
                    "rubric_published": plan.current_rubric_version is not None,
                    "assigned_count": assigned,
                    "submitted_count": submitted,
                    "completion_ratio": submitted / assigned,
                }
            )
        return Response({"windows": windows, "assignments": assignments})


class JudgeWorkloadView(OrganizerView):
    """S24: organizer-only roll-up of every judge's assigned/submitted
    count across the whole event, sorted least-complete first, so a
    judge falling behind is the first thing an organizer sees. Never
    exposes ballot content -- counts only, the same boundary
    `EvaluationProgressView` already draws for the plan-wide summary.
    """

    @extend_schema(responses=JudgeWorkloadRowSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        plans = list(EvaluationPlan.objects.filter(stage__event=event).select_related("stage"))
        judges = User.objects.filter(
            memberships__workspace=self.get_workspace(), memberships__role=Role.JUDGE
        ).distinct()
        rows = []
        for judge in judges:
            assigned = 0
            submitted = 0
            for plan in plans:
                plan_assigned = _eligible_candidates(plan, judge).count()
                if plan_assigned == 0:
                    continue
                assigned += plan_assigned
                submitted += Ballot.objects.filter(
                    rubric_version__plan=plan, judge=judge, is_calibration=False
                ).count()
            if assigned == 0:
                continue
            rows.append(
                {
                    "judge": judge.username,
                    "assigned_count": assigned,
                    "submitted_count": submitted,
                    "completion_ratio": submitted / assigned,
                }
            )
        return Response(sorted(rows, key=lambda row: row["completion_ratio"]))


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
        previous = plan.current_rubric_version
        next_number = (previous.number + 1) if previous else 1
        try:
            with transaction.atomic():
                version = RubricVersion.objects.create(
                    plan=plan, number=next_number, criteria=plan.draft_criteria
                )
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        changes = diff_snapshots(
            {"criteria": previous.criteria if previous else None},
            {"criteria": version.criteria},
        )
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="rubric.published",
            target=version,
            metadata={"event_id": str(self.get_event().public_id), "changes": changes}
            if changes
            else {"event_id": str(self.get_event().public_id)},
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
        if is_conflicted(self.get_event().id, request.user.id, project.id):
            raise ValidationError({"detail": "You have a declared conflict of interest here."})
        if (
            plan.prize_judging
            and not _eligible_candidates(plan, request.user).filter(id=project.id).exists()
        ):
            raise ValidationError({"detail": "You are not eligible to judge this prize candidate."})
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
        if (
            plan.prize_judging
            and not _eligible_candidates(plan, request.user).filter(id=project.id).exists()
        ):
            raise ValidationError({"detail": "You are not eligible to judge this prize candidate."})
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


class JudgeCOIRelationshipView(OrganizerView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(responses=JudgeCOIRelationshipSerializer(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        rows = JudgeCOIRelationship.objects.filter(event=self.get_event())
        if not has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN):
            rows = rows.filter(judge=request.user)
        return Response(
            JudgeCOIRelationshipSerializer(
                rows.select_related("judge", "team", "declared_by"), many=True
            ).data
        )

    @extend_schema(
        request=JudgeCOIRelationshipInputSchema,
        responses={201: JudgeCOIRelationshipSerializer},
    )
    @transaction.atomic
    def post(self, request, workspace_public_id, event_public_id):
        schema = JudgeCOIRelationshipInputSchema(data=request.data)
        schema.is_valid(raise_exception=True)
        data = schema.validated_data
        organizer = has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN)
        if not organizer and data.get("judge") not in (None, request.user.public_id):
            raise PermissionDenied("Judges can declare only their own relationships.")
        judge = (
            get_object_or_404(User, public_id=data["judge"])
            if organizer and data.get("judge")
            else request.user
        )
        if not has_any_role(judge, self.get_workspace(), Role.JUDGE):
            raise ValidationError({"judge": "User must judge in this workspace."})
        team = (
            get_object_or_404(Team, event=self.get_event(), public_id=data["team"])
            if data.get("team")
            else None
        )
        row = JudgeCOIRelationship(
            event=self.get_event(),
            judge=judge,
            kind=data["kind"],
            team=team,
            value=data.get("value", ""),
            declared_by=request.user,
        )
        try:
            row.full_clean()
            row.save()
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        except IntegrityError as exc:
            raise ValidationError({"detail": "Relationship is already declared."}) from exc
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="conflict_relationship.declared",
            target=row,
        )
        return Response(JudgeCOIRelationshipSerializer(row).data, status=201)


class JudgeCOIRelationshipDetailView(OrganizerView):
    @extend_schema(responses={204: None})
    @transaction.atomic
    def delete(self, request, workspace_public_id, event_public_id, relationship_public_id):
        row = get_object_or_404(
            JudgeCOIRelationship, event=self.get_event(), public_id=relationship_public_id
        )
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="conflict_relationship.removed",
            target=row,
            metadata={"judge_id": row.judge_id, "kind": row.kind},
        )
        row.delete()
        return Response(status=204)


class ProjectCOIAttributeView(OrganizerView):
    @extend_schema(responses=ProjectCOIAttributeSerializer(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        rows = ProjectCOIAttribute.objects.filter(project__event=self.get_event())
        return Response(
            ProjectCOIAttributeSerializer(rows.select_related("project"), many=True).data
        )

    @extend_schema(
        request=ProjectCOIAttributeInputSchema,
        responses={201: ProjectCOIAttributeSerializer},
    )
    @transaction.atomic
    def post(self, request, workspace_public_id, event_public_id):
        schema = ProjectCOIAttributeInputSchema(data=request.data)
        schema.is_valid(raise_exception=True)
        data = schema.validated_data
        project = get_object_or_404(Project, event=self.get_event(), public_id=data["project"])
        row = ProjectCOIAttribute(project=project, kind=data["kind"], value=data["value"])
        try:
            row.full_clean()
            row.save()
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        except IntegrityError as exc:
            raise ValidationError({"detail": "Attribute is already recorded."}) from exc
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="conflict_project_attribute.recorded",
            target=row,
        )
        return Response(ProjectCOIAttributeSerializer(row).data, status=201)


class ProjectCOIAttributeDetailView(OrganizerView):
    @extend_schema(responses={204: None})
    @transaction.atomic
    def delete(self, request, workspace_public_id, event_public_id, attribute_public_id):
        row = get_object_or_404(
            ProjectCOIAttribute,
            project__event=self.get_event(),
            public_id=attribute_public_id,
        )
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="conflict_project_attribute.removed",
            target=row,
            metadata={"project_id": row.project_id, "kind": row.kind},
        )
        row.delete()
        return Response(status=204)


class COIRuleView(OrganizerView):
    @extend_schema(responses=COIRuleOutputSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        stored = dict(COIRule.objects.filter(event=self.get_event()).values_list("kind", "enabled"))
        return Response(
            [{"kind": kind, "enabled": stored.get(kind, True)} for kind in COIRuleKind.values]
        )

    @extend_schema(request=COIRuleInputSchema, responses=COIRuleOutputSchema)
    @transaction.atomic
    def put(self, request, workspace_public_id, event_public_id):
        schema = COIRuleInputSchema(data=request.data)
        schema.is_valid(raise_exception=True)
        data = schema.validated_data
        rule, _ = COIRule.objects.update_or_create(
            event=self.get_event(), kind=data["kind"], defaults={"enabled": data["enabled"]}
        )
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="conflict_rule.updated",
            target=rule,
            metadata={"kind": rule.kind, "enabled": rule.enabled},
        )
        return Response({"kind": rule.kind, "enabled": rule.enabled})


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


class AssignmentPreviewView(PlanMixin):
    """S04: preview what `activate` would produce for one or more coverage
    values, without writing anything -- an organizer can compare coverage/
    load/conflict/expertise(-via-connectivity) before committing to an
    activation, which is otherwise immutable once created.
    """

    @extend_schema(
        request=AssignmentPreviewInputSchema, responses=AssignmentCoveragePreviewSchema(many=True)
    )
    def post(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        coverage_options = request.data.get("coverage_options") or [3]
        if (
            not isinstance(coverage_options, list)
            or not coverage_options
            or len(coverage_options) > 10
            or any(not isinstance(v, int) or isinstance(v, bool) or v < 1 for v in coverage_options)
        ):
            raise ValidationError({"coverage_options": "Must be 1-10 positive integers."})
        try:
            previews = [preview_assignment(plan, coverage=value) for value in coverage_options]
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(previews)


class AssignmentCompareView(PlanMixin):
    """VS01: side-by-side evidence for the existing greedy heuristic and
    the explicit min-cost-flow optimization solver, read-only like
    AssignmentPreviewView. Only meaningful for the assigned-subset
    strategy (see evaluations.optimization).
    """

    @extend_schema(request=AssignmentCompareInputSchema, responses=AssignmentCompareSchema)
    def post(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        coverage = request.data.get("coverage", 3)
        if not isinstance(coverage, int) or isinstance(coverage, bool) or coverage < 1:
            raise ValidationError({"coverage": "Must be a positive integer."})
        try:
            result = compare_assignments(plan, coverage=coverage)
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(result)


class AssignmentActivateOptimizedView(PlanMixin):
    """VS01: freezes a new AssignmentVersion from the optimization solver
    and makes it active -- same model, same immutability, same audit
    trail as AssignmentActivateView; only `evidence["solver"]` and which
    pure function computed the pairing differ.
    """

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
                version = activate_optimized(plan, coverage=coverage)
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


class AssignmentRebalanceView(PlanMixin):
    """S05: recover an assigned-subset plan's active assignment after judge
    dropout/backlog -- keeps every already-submitted ballot's pairing,
    reassigns each dropped judge's pending load to the remaining pool, and
    re-repairs connectivity. Freezes a new AssignmentVersion; the previous
    one is untouched.
    """

    @extend_schema(
        request=AssignmentRebalanceInputSchema, responses={201: AssignmentVersionSerializer}
    )
    @transaction.atomic
    def post(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        drop_judge_public_ids = request.data.get("drop_judges", [])
        if not isinstance(drop_judge_public_ids, list):
            raise ValidationError({"drop_judges": "Must be a list of judge ids."})
        drop_judges = User.objects.filter(public_id__in=drop_judge_public_ids)
        if drop_judges.count() != len(set(drop_judge_public_ids)):
            raise ValidationError({"drop_judges": "All ids must be known users."})
        coverage = request.data.get("coverage")
        if coverage is not None and (
            not isinstance(coverage, int) or isinstance(coverage, bool) or coverage < 1
        ):
            raise ValidationError({"coverage": "Must be a positive integer."})
        try:
            with transaction.atomic():
                version = rebalance(
                    plan,
                    drop_judge_ids=set(drop_judges.values_list("id", flat=True)),
                    coverage=coverage,
                )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="assignment.rebalanced",
            target=version,
            metadata=version.evidence,
        )
        return Response(AssignmentVersionSerializer(version).data, status=201)


class AssignmentDropoutSimulationView(PlanMixin):
    """Preview assignment fragility with one or more pool judges absent."""

    @extend_schema(request=DropoutSimulationInputSchema, responses=DropoutSimulationSchema)
    def post(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        schema = DropoutSimulationInputSchema(data=request.data)
        schema.is_valid(raise_exception=True)
        scenarios = schema.validated_data["drop_scenarios"]
        if any(len(set(scenario)) != len(scenario) for scenario in scenarios):
            raise ValidationError({"drop_scenarios": "A scenario cannot repeat a judge."})

        requested_ids = {public_id for scenario in scenarios for public_id in scenario}
        pool_judges = {
            public_id: judge_id
            for public_id, judge_id in PoolMembership.objects.filter(
                pool_id=plan.pool_id, judge__public_id__in=requested_ids
            ).values_list("judge__public_id", "judge_id")
        }
        if requested_ids != pool_judges.keys():
            raise ValidationError({"drop_scenarios": "All judges must belong to this plan's pool."})

        try:
            results = [
                simulate_dropout(plan, drop_judge_ids={pool_judges[j] for j in scenario})
                for scenario in scenarios
            ]
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc

        project_ids = {gap["project_id"] for result in results for gap in result["coverage_gaps"]}
        projects = Project.objects.in_bulk(project_ids)
        for requested, result in zip(scenarios, results):
            result["drop_judges"] = [str(public_id) for public_id in requested]
            result["coverage_gaps"] = [
                {"project": str(projects[gap["project_id"]].public_id), "missing": gap["missing"]}
                for gap in result["coverage_gaps"]
            ]
        return Response(
            {
                "active_version": str(plan.active_assignment_version.public_id),
                "baseline": plan.active_assignment_version.evidence,
                "scenarios": results,
            }
        )


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


class CloseCallsView(PlanMixin):
    """VS03: organizer-only preview of a rubric plan's current close
    calls -- the exact bounded set a linked pairwise `hybrid_source` plan
    would restrict its eligible candidates to -- so an organizer can
    decide whether a tie-break round is worth setting up before creating
    one. Read-only; computes from the plan's own latest normalization
    run, never a live re-scan of in-progress ballots.
    """

    @extend_schema(responses=CloseCallsSchema)
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        if plan.mode != EvaluationMode.RUBRIC:
            raise ValidationError({"detail": "Close calls apply to a rubric-mode plan."})
        latest_run = plan.normalization_runs.order_by("-number").first()
        if latest_run is None:
            return Response({"normalization_run": None, "projects": []})
        close_ids = close_call_project_ids(plan, latest_run)
        projects = Project.objects.filter(id__in=close_ids)
        return Response(
            {
                "normalization_run": latest_run.number,
                "projects": [str(p.public_id) for p in projects],
            }
        )


_SENSITIVITY_SCENARIO_SCHEMA = {
    "type": "object",
    "properties": {
        "order": {"type": "array", "items": {"type": "string", "format": "uuid"}},
        "rank_changed": {"type": "boolean"},
    },
}
_SENSITIVITY_DIMENSION_SCHEMA = {
    "type": "object",
    "properties": {
        "baseline": {"type": "array", "items": {"type": "string", "format": "uuid"}},
        "scenarios": {"type": "object", "additionalProperties": _SENSITIVITY_SCENARIO_SCHEMA},
    },
}


def _translate_sensitivity_dimension(block, projects_by_id, *, key_names=None):
    def order(ids):
        return [str(projects_by_id[pid].public_id) for pid in ids if pid in projects_by_id]

    def scenario_key(raw_key):
        if key_names is None:
            return raw_key
        return key_names.get(int(raw_key), raw_key)

    return {
        "baseline": order(block["baseline"]),
        "scenarios": {
            scenario_key(key): {
                "order": order(value["order"]),
                "rank_changed": value["rank_changed"],
            }
            for key, value in block["scenarios"].items()
        },
    }


def _valid_ridge_lambda(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


class SensitivityExplorerView(PlanMixin):
    """Read-only what-if ranking over the plan's current live ballots."""

    @extend_schema(
        request=SensitivityInputSchema,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "ridge_lambda": _SENSITIVITY_DIMENSION_SCHEMA,
                    "judge_removal": _SENSITIVITY_DIMENSION_SCHEMA,
                    "incompleteness": _SENSITIVITY_DIMENSION_SCHEMA,
                },
            }
        },
    )
    def post(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        if plan.mode != EvaluationMode.RUBRIC:
            raise ValidationError({"detail": "Sensitivity analysis applies to a rubric-mode plan."})
        ridge_lambdas = request.data.get("ridge_lambdas", list(DEFAULT_RIDGE_LAMBDAS))
        holdout_counts = request.data.get("holdout_counts", list(DEFAULT_HOLDOUT_COUNTS))
        if (
            not isinstance(ridge_lambdas, list)
            or len(ridge_lambdas) > 10
            or any(not _valid_ridge_lambda(v) for v in ridge_lambdas)
        ):
            raise ValidationError({"ridge_lambdas": "Must be 0-10 nonnegative numbers."})
        if (
            not isinstance(holdout_counts, list)
            or len(holdout_counts) > 10
            or any(not isinstance(v, int) or isinstance(v, bool) or v < 1 for v in holdout_counts)
        ):
            raise ValidationError({"holdout_counts": "Must be 0-10 positive integers."})

        observations = chronological_observations(plan)
        ridge_result = ridge_lambda_sensitivity(observations, ridge_lambdas=ridge_lambdas)
        judge_result = judge_removal_sensitivity(observations)
        incompleteness_result = incompleteness_sensitivity(
            observations, holdout_counts=holdout_counts
        )

        all_ids = {
            project_id
            for block in (ridge_result, judge_result, incompleteness_result)
            for project_id in block["baseline"]
        }
        for block in (ridge_result, judge_result, incompleteness_result):
            for scenario in block["scenarios"].values():
                all_ids.update(scenario["order"])
        projects_by_id = {p.id: p for p in Project.objects.filter(id__in=all_ids)}
        judge_ids = [int(judge_id) for judge_id in judge_result["scenarios"]]
        usernames_by_id = {u.id: u.username for u in User.objects.filter(id__in=judge_ids)}

        return Response(
            {
                "ridge_lambda": _translate_sensitivity_dimension(ridge_result, projects_by_id),
                "judge_removal": _translate_sensitivity_dimension(
                    judge_result, projects_by_id, key_names=usernames_by_id
                ),
                "incompleteness": _translate_sensitivity_dimension(
                    incompleteness_result, projects_by_id
                ),
            }
        )


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


class JudgingProvenanceView(PlanMixin):
    """Trace a published rubric result to frozen authored scores and awards."""

    @extend_schema(responses=ProvenanceSchema)
    def get(
        self,
        request,
        workspace_public_id,
        event_public_id,
        stage_public_id,
        plan_public_id,
        project_public_id,
    ):
        plan = self.get_plan()
        if plan.mode != EvaluationMode.RUBRIC or plan.published_normalization_run_id is None:
            return Response({"detail": "No rubric results have been published."}, status=404)
        project = get_object_or_404(Project, event=self.get_event(), public_id=project_public_id)
        run = plan.published_normalization_run
        result = next(
            (row for row in ranked_results(plan, run) if row.project_id == project.id), None
        )
        if result is None:
            return Response({"detail": "Project is absent from this published run."}, status=404)

        frozen_ballots = run.evidence.get("ballots")
        ballots = None
        if frozen_ballots is not None:
            ballots = [
                {
                    **{
                        key: value
                        for key, value in ballot.items()
                        if key not in {"judge_id", "project_id"}
                    },
                    "judge_effect": run.evidence["judge_effects"].get(str(ballot["judge_id"]), 0.0),
                }
                for ballot in frozen_ballots
                if ballot["project_id"] == project.id
            ]

        award_winners = AwardWinner.objects.filter(
            award__evaluation_plan=plan, project=project, source=SelectionSource.EVALUATION
        ).select_related("award")
        awards = [
            {
                "award": str(winner.award.public_id),
                "name": winner.award.name,
                "winner": str(winner.public_id),
                "rank_at_selection": winner.evidence.get("rank"),
                "override_reason": winner.override_reason,
                "published": winner.award.published_at is not None,
            }
            for winner in award_winners
            if winner.evidence.get("normalization_run") == str(run.public_id)
        ]
        return Response(
            {
                "project": str(project.public_id),
                "project_name": project.name,
                "rank": result.rank,
                "raw_score": result.raw_score,
                "final_score": result.final_score,
                "tie_break": result.tie_break,
                "normalization_run": str(run.public_id),
                "ridge_lambda": run.ridge_lambda,
                "converged": run.converged,
                "grand_mean": run.grand_mean,
                "ballot_snapshot_available": ballots is not None,
                "ballots": ballots,
                "awards": awards,
            }
        )


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


class ProjectFeedbackView(PlanMixin):
    """S21: a project's released judge feedback (`Ballot.comment`) --
    never shown until the organizer opts the plan into
    `feedback_visible_to_participants`, and never with judge identity
    unless the organizer also opts out of `feedback_anonymous`. Scoped to
    one project (unlike the plan-wide `ResultsView`): a participant may
    only ever read their own project's feedback.
    """

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.PARTICIPANT, Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(responses=FeedbackEntrySchema(many=True))
    def get(
        self,
        request,
        workspace_public_id,
        event_public_id,
        stage_public_id,
        plan_public_id,
        project_public_id,
    ):
        plan = self.get_plan()
        project = get_object_or_404(Project, event=self.get_event(), public_id=project_public_id)
        is_organizer = has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN)
        if not is_organizer:
            if not plan.feedback_visible_to_participants:
                raise PermissionDenied("Feedback has not been released for this plan.")
            if not project.memberships.filter(user=request.user).exists():
                return Response(status=404)
        ballots = (
            Ballot.objects.filter(rubric_version__plan=plan, project=project, is_calibration=False)
            .exclude(comment="")
            .select_related("judge")
            .order_by("submitted_at")
        )
        return Response(
            [
                {
                    "judge": None if plan.feedback_anonymous else ballot.judge.username,
                    "comment": ballot.comment,
                    "submitted_at": ballot.submitted_at,
                }
                for ballot in ballots
            ]
        )


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

        # S06: under blind judging, ordering by the real name would leak an
        # alphabetical-by-identity signal into the queue itself -- order by
        # public_id (stable, identity-independent) instead.
        candidates = _eligible_candidates(plan, request.user).order_by(
            "public_id" if plan.blind_judging else "name"
        )

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
                    "name": (
                        anonymize.anonymized_label(plan.id, project.public_id)
                        if plan.blind_judging
                        else project.name
                    ),
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
    """S01/VS02: the next pair of candidates for the requesting judge to
    compare under a PAIRWISE-mode plan. Adaptive (VS02): once at least
    one PairwiseRun exists, prefers the not-yet-compared-by-this-judge
    pair whose current Bradley-Terry strengths are closest -- the most
    informative comparison to run next -- among candidates still within
    a bounded coverage-fairness window (see pairwise.select_next_pair);
    before any run exists there is no ranking uncertainty to reduce yet,
    so it falls back to the original minimal-comparison-count choice.
    Returns null once every eligible pair has been judged (or fewer than
    two eligible candidates exist).
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

        latest_run = plan.pairwise_runs.order_by("-number").first()
        strengths = (
            {
                int(project_id): data["strength"]
                for project_id, data in latest_run.evidence["projects"].items()
            }
            if latest_run
            else None
        )
        best_pair = pairwise.select_next_pair(
            candidate_ids, already_compared, comparison_counts, strengths
        )

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

        if any(
            is_conflicted(event.id, request.user.id, project.id)
            for project in (project_a, project_b)
        ):
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
        plan = self.get_plan()
        if (
            plan.prize_judging
            and not has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN)
            and not PoolMembership.objects.filter(pool_id=plan.pool_id, judge=request.user).exists()
        ):
            raise PermissionDenied("You are not in this prize judging pool.")
        projects = plan.calibration_projects.all()
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
        if (
            plan.prize_judging
            and not PoolMembership.objects.filter(pool_id=plan.pool_id, judge=request.user).exists()
        ):
            raise ValidationError({"detail": "You are not in this prize judging pool."})
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


class AgreementSummaryView(PlanMixin):
    """S03: organizer-only, honest inter-rater agreement diagnostics -- real
    per-criterion score dispersion and judge-pair ranking correlation
    computed live from current ballots, never persisted or "run" (this is
    an exploratory diagnostic, not evidence a published result is drawn
    from). A statistic backed by too little data is reported as such
    (`tau: null`) rather than a misleadingly confident number -- see
    evaluations/agreement.py.
    """

    @extend_schema(responses=AgreementSummarySchema)
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        if plan.mode != EvaluationMode.RUBRIC:
            raise ValidationError({"detail": "Agreement analytics apply to rubric-mode plans."})

        criterion_results = agreement.criterion_disagreement(agreement.criterion_responses(plan))
        judge_scores = agreement.judge_weighted_scores(plan)
        rank_results = agreement.pairwise_rank_agreement(judge_scores)

        project_ids = {r.project_id for r in criterion_results} | {
            pid for scores in judge_scores.values() for pid in scores
        }
        judge_ids = {j for r in rank_results for j in (r.judge_a, r.judge_b)} | set(judge_scores)
        projects_by_id = {p.id: p for p in Project.objects.filter(id__in=project_ids)}
        judges_by_id = {u.id: u for u in User.objects.filter(id__in=judge_ids)}

        return Response(
            {
                "criteria": [
                    {
                        "project": str(projects_by_id[r.project_id].public_id),
                        "project_name": projects_by_id[r.project_id].name,
                        "criterion_id": r.criterion_id,
                        "scores": {
                            str(judges_by_id[j].public_id): score for j, score in r.scores.items()
                        },
                        "mean": r.mean,
                        "range": r.range,
                        "stdev": r.stdev,
                    }
                    for r in criterion_results
                ],
                "rankings": [
                    {
                        "judge_a": str(judges_by_id[r.judge_a].public_id),
                        "judge_b": str(judges_by_id[r.judge_b].public_id),
                        "shared_candidates": r.shared_candidates,
                        "tau": r.tau,
                    }
                    for r in rank_results
                ],
            }
        )
