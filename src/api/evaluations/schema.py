from rest_framework import serializers

from .serializers import BallotResponseSerializer


class AssignmentActivateInputSchema(serializers.Serializer):
    coverage = serializers.IntegerField(min_value=1, required=False)


class PoolMembershipInputSchema(serializers.Serializer):
    judge = serializers.UUIDField()
    track_expertise = serializers.ListField(child=serializers.UUIDField(), required=False)


class NormalizationInputSchema(serializers.Serializer):
    ridge_lambda = serializers.FloatField(min_value=0, required=False)


class BallotSubmitInputSchema(serializers.Serializer):
    project = serializers.UUIDField()
    comment = serializers.CharField(allow_blank=True, required=False)
    responses = BallotResponseSerializer(many=True)


class BallotDraftInputSchema(serializers.Serializer):
    responses = serializers.JSONField(required=False)
    comment = serializers.CharField(allow_blank=True, required=False)


class CandidateQueueItemSchema(serializers.Serializer):
    project = serializers.UUIDField()
    name = serializers.CharField()
    status = serializers.ChoiceField(choices=["pending", "drafted", "submitted"])


class NormalizationProgressSchema(serializers.Serializer):
    number = serializers.IntegerField()
    converged = serializers.BooleanField()
    low_information_judges = serializers.IntegerField()


class EvaluationProgressSchema(serializers.Serializer):
    candidate_count = serializers.IntegerField()
    pool_judge_count = serializers.IntegerField()
    conflict_count = serializers.IntegerField()
    expected_ballots = serializers.IntegerField(allow_null=True)
    submitted_ballots = serializers.IntegerField()
    completion_ratio = serializers.FloatField(allow_null=True)
    rubric_published = serializers.BooleanField()
    assignment_active = serializers.BooleanField()
    latest_normalization_run = NormalizationProgressSchema(allow_null=True)
    results_published = serializers.BooleanField()


class ResultsPublishInputSchema(serializers.Serializer):
    normalization_run = serializers.UUIDField()
    tie_breaks = serializers.DictField(child=serializers.IntegerField(), required=False)


class RankedResultSchema(serializers.Serializer):
    rank = serializers.IntegerField()
    project = serializers.UUIDField(allow_null=True)
    project_name = serializers.CharField(allow_null=True)
    raw_score = serializers.FloatField(allow_null=True)
    final_score = serializers.FloatField()
    tie_break = serializers.IntegerField(allow_null=True)
