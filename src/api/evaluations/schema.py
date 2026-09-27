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


class CalibrationOverviewSchema(serializers.Serializer):
    required = serializers.BooleanField()
    project_count = serializers.IntegerField()
    judges_total = serializers.IntegerField()
    judges_complete = serializers.IntegerField()


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
    calibration = CalibrationOverviewSchema(allow_null=True)


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


class ProvenanceCriterionSchema(serializers.Serializer):
    criterion_id = serializers.CharField()
    criterion_name = serializers.CharField()
    weight = serializers.FloatField()
    score = serializers.FloatField()


class ProvenanceBallotSchema(serializers.Serializer):
    ballot = serializers.UUIDField()
    judge = serializers.UUIDField()
    rubric_version = serializers.UUIDField()
    responses = ProvenanceCriterionSchema(many=True)
    weighted_score = serializers.FloatField()
    judge_effect = serializers.FloatField()
    adjusted_score = serializers.FloatField()
    submitted_at = serializers.DateTimeField()


class ProvenanceAwardSchema(serializers.Serializer):
    award = serializers.UUIDField()
    name = serializers.CharField()
    winner = serializers.UUIDField()
    rank_at_selection = serializers.IntegerField(allow_null=True)
    override_reason = serializers.CharField()
    published = serializers.BooleanField()


class ProvenanceSchema(serializers.Serializer):
    project = serializers.UUIDField()
    project_name = serializers.CharField()
    rank = serializers.IntegerField()
    raw_score = serializers.FloatField(allow_null=True)
    final_score = serializers.FloatField()
    tie_break = serializers.IntegerField(allow_null=True)
    normalization_run = serializers.UUIDField()
    ridge_lambda = serializers.FloatField()
    converged = serializers.BooleanField()
    grand_mean = serializers.FloatField()
    ballot_snapshot_available = serializers.BooleanField()
    ballots = ProvenanceBallotSchema(many=True, allow_null=True)
    awards = ProvenanceAwardSchema(many=True)


class FeedbackEntrySchema(serializers.Serializer):
    judge = serializers.CharField(allow_null=True)
    comment = serializers.CharField()
    submitted_at = serializers.DateTimeField()


class CalendarWindowSchema(serializers.Serializer):
    name = serializers.CharField()
    opens_at = serializers.DateTimeField(allow_null=True)
    closes_at = serializers.DateTimeField(allow_null=True)
    status = serializers.ChoiceField(choices=["not_yet_open", "open", "closed"])


class CalendarAssignmentSchema(serializers.Serializer):
    stage_name = serializers.CharField()
    plan = serializers.UUIDField()
    plan_name = serializers.CharField()
    rubric_published = serializers.BooleanField()
    assigned_count = serializers.IntegerField()
    submitted_count = serializers.IntegerField()
    completion_ratio = serializers.FloatField(allow_null=True)


class JudgeCalendarSchema(serializers.Serializer):
    windows = CalendarWindowSchema(many=True)
    assignments = CalendarAssignmentSchema(many=True)


class JudgeWorkloadRowSchema(serializers.Serializer):
    judge = serializers.CharField()
    assigned_count = serializers.IntegerField()
    submitted_count = serializers.IntegerField()
    completion_ratio = serializers.FloatField()


class CloseCallsSchema(serializers.Serializer):
    normalization_run = serializers.IntegerField(allow_null=True)
    projects = serializers.ListField(child=serializers.UUIDField())


class SensitivityInputSchema(serializers.Serializer):
    ridge_lambdas = serializers.ListField(
        child=serializers.FloatField(min_value=0), required=False, max_length=10
    )
    holdout_counts = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False, max_length=10
    )


class PairwiseComparisonInputSchema(serializers.Serializer):
    project_a = serializers.UUIDField()
    project_b = serializers.UUIDField()
    winner = serializers.UUIDField(required=False, allow_null=True)


class PairwiseNextPairSchema(serializers.Serializer):
    project_a = serializers.UUIDField()
    project_b = serializers.UUIDField()


class PairwiseRunInputSchema(serializers.Serializer):
    prior_games = serializers.FloatField(min_value=0, required=False)


class PairwiseResultsPublishInputSchema(serializers.Serializer):
    pairwise_run = serializers.UUIDField()
    tie_breaks = serializers.DictField(child=serializers.IntegerField(), required=False)


class AssignmentRebalanceInputSchema(serializers.Serializer):
    drop_judges = serializers.ListField(child=serializers.UUIDField(), required=False)
    coverage = serializers.IntegerField(min_value=1, required=False)


class DropoutSimulationInputSchema(serializers.Serializer):
    drop_scenarios = serializers.ListField(
        child=serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=10),
        min_length=1,
        max_length=10,
    )


class DropoutCoverageGapSchema(serializers.Serializer):
    project = serializers.UUIDField()
    missing = serializers.IntegerField()


class DropoutScenarioSchema(serializers.Serializer):
    drop_judges = serializers.ListField(child=serializers.UUIDField())
    evidence = serializers.DictField()
    pending_removed = serializers.IntegerField()
    assignments_added = serializers.IntegerField()
    coverage_gaps = DropoutCoverageGapSchema(many=True)


class DropoutSimulationSchema(serializers.Serializer):
    active_version = serializers.UUIDField()
    baseline = serializers.DictField()
    scenarios = DropoutScenarioSchema(many=True)


class AssignmentPreviewInputSchema(serializers.Serializer):
    coverage_options = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False
    )


class AssignmentCoveragePreviewSchema(serializers.Serializer):
    solver = serializers.CharField()
    coverage = serializers.IntegerField()
    candidate_count = serializers.IntegerField()
    judge_count = serializers.IntegerField()
    assignment_count = serializers.IntegerField()
    load_by_judge = serializers.DictField(child=serializers.IntegerField())
    conflict_count = serializers.IntegerField()
    connectivity = serializers.DictField()


class AssignmentCompareInputSchema(serializers.Serializer):
    coverage = serializers.IntegerField(min_value=1, required=False)


class AssignmentCompareSchema(serializers.Serializer):
    heuristic = AssignmentCoveragePreviewSchema()
    optimized = AssignmentCoveragePreviewSchema()


class AgreementCriterionSchema(serializers.Serializer):
    project = serializers.UUIDField()
    project_name = serializers.CharField()
    criterion_id = serializers.CharField()
    scores = serializers.DictField(child=serializers.FloatField())
    mean = serializers.FloatField()
    range = serializers.FloatField()
    stdev = serializers.FloatField()


class AgreementRankingSchema(serializers.Serializer):
    judge_a = serializers.UUIDField()
    judge_b = serializers.UUIDField()
    shared_candidates = serializers.IntegerField()
    tau = serializers.FloatField(allow_null=True)


class AgreementSummarySchema(serializers.Serializer):
    criteria = AgreementCriterionSchema(many=True)
    rankings = AgreementRankingSchema(many=True)


class CalibrationProjectsInputSchema(serializers.Serializer):
    projects = serializers.ListField(child=serializers.UUIDField())


class CalibrationProjectItemSchema(serializers.Serializer):
    project = serializers.UUIDField()
    name = serializers.CharField()


class CalibrationStatusSchema(serializers.Serializer):
    required = serializers.BooleanField()
    total = serializers.IntegerField()
    completed = serializers.ListField(child=serializers.UUIDField())
    remaining = serializers.ListField(child=serializers.UUIDField())
    is_complete = serializers.BooleanField()


class CalibrationCriterionSummarySchema(serializers.Serializer):
    criterion_id = serializers.CharField()
    scores = serializers.DictField(child=serializers.FloatField())
    min = serializers.FloatField()
    max = serializers.FloatField()
    mean = serializers.FloatField()
    spread = serializers.FloatField()


class CalibrationProjectSummarySchema(serializers.Serializer):
    project = serializers.UUIDField()
    project_name = serializers.CharField()
    criteria = CalibrationCriterionSummarySchema(many=True)


class PairwiseRankedResultSchema(serializers.Serializer):
    rank = serializers.IntegerField()
    project = serializers.UUIDField(allow_null=True)
    project_name = serializers.CharField(allow_null=True)
    strength = serializers.FloatField()
    win_count = serializers.FloatField()
    comparison_count = serializers.FloatField()
    tie_break = serializers.IntegerField(allow_null=True)
