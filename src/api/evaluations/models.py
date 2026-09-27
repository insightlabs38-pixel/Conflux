from core.models import PublicIdModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from projects.models import Project
from stages.models import Stage

from .rubric import clean_criteria


class EvaluationCandidateType(models.TextChoices):
    PROJECT = "project", "Project"


class EvaluationPoolStrategy(models.TextChoices):
    ALL_JUDGES = "all_judges", "All judges score every candidate"
    ASSIGNED_SUBSET = "assigned_subset", "Judges score an assigned subset"


class EvaluationPlan(PublicIdModel):
    """Unified evaluation abstraction (JDG-001): what's being judged, by
    whom, and whether feedback is visible to participants. Pool assignment
    itself (who is actually assigned what) is C-B14's job.
    """

    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name="evaluation_plans")
    name = models.CharField(max_length=160)
    candidate_type = models.CharField(
        max_length=20,
        choices=EvaluationCandidateType.choices,
        default=EvaluationCandidateType.PROJECT,
    )
    pool_strategy = models.CharField(
        max_length=20,
        choices=EvaluationPoolStrategy.choices,
        default=EvaluationPoolStrategy.ALL_JUDGES,
    )
    results_visible_to_participants = models.BooleanField(default=False)
    draft_criteria = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["stage", "name"], name="unique_evaluation_plan_name")
        ]

    @property
    def current_rubric_version(self):
        return self.rubric_versions.order_by("-number").first()


class RubricVersion(PublicIdModel):
    """A published, immutable snapshot of an EvaluationPlan's criteria; a
    Ballot always scores against one specific version, so reweighting a
    rubric later can never retroactively change an already-cast ballot's
    meaning (mirrors FormVersion/SubmissionVersion's immutability pattern).
    """

    plan = models.ForeignKey(
        EvaluationPlan, on_delete=models.PROTECT, related_name="rubric_versions"
    )
    number = models.PositiveIntegerField()
    criteria = models.JSONField()
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["plan", "number"], name="unique_rubric_version")
        ]
        ordering = ["number"]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Published rubric versions are immutable.")
        self.criteria = clean_criteria(self.criteria)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Published rubric versions are immutable.")


class Ballot(PublicIdModel):
    """One judge's private, submitted evaluation of one candidate against one
    rubric version (JDG-003). Never readable by another judge or by the
    candidate's participants -- see evaluations.views for the isolation
    check (same shape as the T2 judge-isolation invariant elsewhere).
    """

    rubric_version = models.ForeignKey(
        RubricVersion, on_delete=models.PROTECT, related_name="ballots"
    )
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ballots"
    )
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="ballots")
    comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["rubric_version", "judge", "project"], name="unique_ballot"
            )
        ]

    def clean(self):
        if self.project.event_id != self.rubric_version.plan.stage.event_id:
            raise ValidationError({"project": "Project must belong to the plan's event."})


class BallotResponse(PublicIdModel):
    ballot = models.ForeignKey(Ballot, on_delete=models.CASCADE, related_name="responses")
    criterion_id = models.CharField(max_length=64)
    score = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ballot", "criterion_id"], name="unique_ballot_response"
            )
        ]

    def clean(self):
        criteria = {c["id"]: c for c in self.ballot.rubric_version.criteria}
        criterion = criteria.get(self.criterion_id)
        if criterion is None:
            raise ValidationError({"criterion_id": "Not a criterion on this rubric version."})
        if not (criterion["min_score"] <= self.score <= criterion["max_score"]):
            raise ValidationError(
                {
                    "score": (
                        f"Must be between {criterion['min_score']} and {criterion['max_score']}."
                    )
                }
            )
