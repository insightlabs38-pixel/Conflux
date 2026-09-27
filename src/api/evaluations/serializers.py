from django.core.exceptions import ValidationError as ModelValidationError
from rest_framework import serializers

from .models import Ballot, BallotResponse, EvaluationPlan, RubricVersion
from .rubric import clean_criteria


class EvaluationPlanSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    current_rubric_version = serializers.SerializerMethodField()

    class Meta:
        model = EvaluationPlan
        fields = [
            "public_id",
            "name",
            "candidate_type",
            "pool_strategy",
            "results_visible_to_participants",
            "draft_criteria",
            "current_rubric_version",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_current_rubric_version(self, plan):
        version = plan.current_rubric_version
        return version.number if version else None

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
