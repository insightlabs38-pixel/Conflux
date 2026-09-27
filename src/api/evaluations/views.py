from accounts.authentication import CookieSessionAuthentication
from audit.services import record_mutation
from core.authz import has_any_role
from core.permissions import require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from projects.models import Project
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from stages.views import StageEventMixin
from workspaces.models import Role

from .models import Ballot, BallotResponse, EvaluationPlan, RubricVersion
from .serializers import BallotSerializer, EvaluationPlanSerializer, RubricVersionSerializer


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
