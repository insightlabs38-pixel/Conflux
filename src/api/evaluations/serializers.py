from django.core.exceptions import ValidationError as ModelValidationError
from rest_framework import serializers

from .models import (
    Assignment,
    AssignmentVersion,
    Ballot,
    BallotDraft,
    BallotResponse,
    ConflictOfInterest,
    EvaluationPlan,
    EvaluationPool,
    NormalizationRun,
    PairwiseComparison,
    PairwiseRun,
    PoolMembership,
    RubricVersion,
)
from .rubric import clean_criteria


class EvaluationPlanSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    pool = serializers.SlugRelatedField(
        slug_field="public_id",
        queryset=EvaluationPool.objects.all(),
        required=False,
        allow_null=True,
    )
    hybrid_source = serializers.SlugRelatedField(
        slug_field="public_id",
        queryset=EvaluationPlan.objects.all(),
        required=False,
        allow_null=True,
    )
    current_rubric_version = serializers.SerializerMethodField()
    active_assignment_version = serializers.SerializerMethodField()
    published_normalization_run = serializers.SerializerMethodField()
    published_pairwise_run = serializers.SerializerMethodField()
    calibration_projects = serializers.SerializerMethodField()

    class Meta:
        model = EvaluationPlan
        fields = [
            "public_id",
            "name",
            "candidate_type",
            "pool_strategy",
            "mode",
            "results_visible_to_participants",
            "feedback_visible_to_participants",
            "feedback_anonymous",
            "draft_criteria",
            "pool",
            "hybrid_source",
            "current_rubric_version",
            "active_assignment_version",
            "published_normalization_run",
            "published_pairwise_run",
            "calibration_projects",
            "calibration_required",
            "blind_judging",
            "prize_judging",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "calibration_projects"]

    def validate(self, attrs):
        plan = self.instance
        if plan and plan.prize_judging != attrs.get("prize_judging", plan.prize_judging):
            raise serializers.ValidationError(
                {"prize_judging": "Judging scope cannot be changed after plan creation."}
            )
        if plan and plan.prize_judging and "pool" in attrs and attrs["pool"] != plan.pool:
            raise serializers.ValidationError(
                {"pool": "A prize judging pool cannot be changed after plan creation."}
            )
        return attrs

    def get_calibration_projects(self, plan) -> list[str]:
        return [
            str(public_id)
            for public_id in plan.calibration_projects.values_list("public_id", flat=True)
        ]

    def get_current_rubric_version(self, plan) -> int | None:
        version = plan.current_rubric_version
        return version.number if version else None

    def get_active_assignment_version(self, plan) -> int | None:
        return plan.active_assignment_version.number if plan.active_assignment_version_id else None

    def get_published_normalization_run(self, plan) -> int | None:
        return (
            plan.published_normalization_run.number if plan.published_normalization_run_id else None
        )

    def get_published_pairwise_run(self, plan) -> int | None:
        return plan.published_pairwise_run.number if plan.published_pairwise_run_id else None

    def validate_draft_criteria(self, value):
        try:
            return clean_criteria(value)
        except ModelValidationError as exc:
            raise serializers.ValidationError(
                exc.message_dict.get("criteria", exc.messages)
            ) from exc


class RubricVersionSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = RubricVersion
        fields = ["public_id", "number", "criteria", "published_at"]


class BallotResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = BallotResponse
        fields = ["criterion_id", "score"]


class BallotSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    project = serializers.UUIDField(source="project.public_id", read_only=True)
    responses = BallotResponseSerializer(many=True)

    class Meta:
        model = Ballot
        fields = ["public_id", "project", "comment", "responses", "submitted_at"]
        read_only_fields = ["submitted_at"]


class BallotDraftSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    project = serializers.UUIDField(source="project.public_id", read_only=True)

    class Meta:
        model = BallotDraft
        fields = ["public_id", "project", "responses", "comment", "updated_at"]
        read_only_fields = ["updated_at"]


class EvaluationPoolSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = EvaluationPool
        fields = ["public_id", "name", "created_at"]
        read_only_fields = ["created_at"]


class PoolMembershipSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    judge = serializers.UUIDField(source="judge.public_id", read_only=True)
    track_expertise = serializers.SlugRelatedField(
        slug_field="public_id", many=True, read_only=True
    )

    class Meta:
        model = PoolMembership
        fields = ["public_id", "judge", "track_expertise", "created_at"]
        read_only_fields = ["created_at"]


class ConflictOfInterestSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    judge = serializers.UUIDField(source="judge.public_id", read_only=True)
    project = serializers.UUIDField(source="project.public_id", read_only=True)

    class Meta:
        model = ConflictOfInterest
        fields = ["public_id", "judge", "project", "reason", "created_at"]
        read_only_fields = ["created_at"]


class AssignmentSerializer(serializers.ModelSerializer):
    judge = serializers.UUIDField(source="judge.public_id", read_only=True)
    project = serializers.UUIDField(source="project.public_id", read_only=True)

    class Meta:
        model = Assignment
        fields = ["judge", "project"]


class AssignmentVersionSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    assignments = AssignmentSerializer(many=True, read_only=True)

    class Meta:
        model = AssignmentVersion
        fields = ["public_id", "number", "coverage", "evidence", "assignments", "created_at"]


class NormalizationRunSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = NormalizationRun
        fields = [
            "public_id",
            "number",
            "ridge_lambda",
            "iterations",
            "converged",
            "grand_mean",
            "evidence",
            "created_at",
        ]


class PairwiseComparisonSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    judge = serializers.UUIDField(source="judge.public_id", read_only=True)
    project_a = serializers.UUIDField(source="project_a.public_id", read_only=True)
    project_b = serializers.UUIDField(source="project_b.public_id", read_only=True)
    winner = serializers.SerializerMethodField()

    class Meta:
        model = PairwiseComparison
        fields = ["public_id", "judge", "project_a", "project_b", "winner", "submitted_at"]
        read_only_fields = ["submitted_at"]

    def get_winner(self, comparison) -> str | None:
        return str(comparison.winner.public_id) if comparison.winner_id else None


class PairwiseRunSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = PairwiseRun
        fields = [
            "public_id",
            "number",
            "prior_games",
            "iterations",
            "converged",
            "evidence",
            "created_at",
        ]
