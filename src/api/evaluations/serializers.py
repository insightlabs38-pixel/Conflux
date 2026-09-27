from django.core.exceptions import ValidationError as ModelValidationError
from rest_framework import serializers

from .models import (
    Assignment,
    AssignmentVersion,
    Ballot,
    BallotResponse,
    ConflictOfInterest,
    EvaluationPlan,
    EvaluationPool,
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
    current_rubric_version = serializers.SerializerMethodField()
    active_assignment_version = serializers.SerializerMethodField()

    class Meta:
        model = EvaluationPlan
        fields = [
            "public_id",
            "name",
            "candidate_type",
            "pool_strategy",
            "results_visible_to_participants",
            "draft_criteria",
            "pool",
            "current_rubric_version",
            "active_assignment_version",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_current_rubric_version(self, plan):
        version = plan.current_rubric_version
        return version.number if version else None

    def get_active_assignment_version(self, plan):
        return plan.active_assignment_version.number if plan.active_assignment_version_id else None

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
