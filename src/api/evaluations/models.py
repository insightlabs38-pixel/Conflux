from core.authz import has_any_role
from core.models import PublicIdModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from events.models import Track
from projects.models import Project
from stages.models import Stage
from workspaces.models import Role

from .rubric import clean_criteria


class EvaluationCandidateType(models.TextChoices):
    PROJECT = "project", "Project"


class EvaluationPoolStrategy(models.TextChoices):
    ALL_JUDGES = "all_judges", "All judges score every candidate"
    ASSIGNED_SUBSET = "assigned_subset", "Judges score an assigned subset"


class EvaluationMode(models.TextChoices):
    RUBRIC = "rubric", "Weighted rubric scoring"
    PAIRWISE = "pairwise", "Head-to-head pairwise comparison"


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
    mode = models.CharField(
        max_length=20,
        choices=EvaluationMode.choices,
        default=EvaluationMode.RUBRIC,
    )
    results_visible_to_participants = models.BooleanField(default=False)
    draft_criteria = models.JSONField(default=list, blank=True)
    pool = models.ForeignKey(
        "EvaluationPool",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="plans",
    )
    active_assignment_version = models.ForeignKey(
        "AssignmentVersion",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    published_normalization_run = models.ForeignKey(
        "NormalizationRun",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    published_pairwise_run = models.ForeignKey(
        "PairwiseRun",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    # {project_public_id: integer} manual override, lower wins ties (JUX-005).
    tie_breaks = models.JSONField(default=dict, blank=True)
    # S02: a shared set of practice candidates every judge scores against
    # the rubric's anchors before live judging -- see Ballot.is_calibration
    # and evaluations/views.py::CalibrationBallotListCreateView. Mutually
    # exclusive with the real candidate pool (Ballot.clean enforces this),
    # so a calibration project is never also a live one for this plan.
    calibration_projects = models.ManyToManyField(
        Project, blank=True, related_name="calibration_plans"
    )
    calibration_required = models.BooleanField(default=False)
    # S06: when set, CandidateListView replaces a candidate's real project
    # name with a deterministic pseudonym for judges (see
    # evaluations/anonymize.py). No institution/affiliation field exists on
    # Project/Team to redact -- this scopes to the one identity signal the
    # product actually exposes to a judge during live judging.
    blind_judging = models.BooleanField(default=False)
    prize_judging = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["stage", "name"], name="unique_evaluation_plan_name")
        ]

    @property
    def current_rubric_version(self):
        return self.rubric_versions.order_by("-number").first()

    def clean(self):
        if self.pool_id and self.pool.event_id != self.stage.event_id:
            raise ValidationError({"pool": "Pool must belong to the plan's event."})
        if self.prize_judging and not self.pool_id:
            raise ValidationError({"pool": "Prize judging requires a judge pool."})
        if (
            self.published_normalization_run_id
            and self.published_normalization_run.plan_id != self.pk
        ):
            raise ValidationError(
                {"published_normalization_run": "Must be a normalization run of this plan."}
            )
        if self.published_pairwise_run_id and self.published_pairwise_run.plan_id != self.pk:
            raise ValidationError(
                {"published_pairwise_run": "Must be a pairwise run of this plan."}
            )


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
    # S02: a calibration ballot scores a shared practice candidate before
    # live judging opens; it is never a live evidence ballot and is always
    # excluded from normalization (see scoring.ballot_observations).
    is_calibration = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["rubric_version", "judge", "project"], name="unique_ballot"
            )
        ]

    def clean(self):
        plan = self.rubric_version.plan
        if self.project.event_id != plan.stage.event_id:
            raise ValidationError({"project": "Project must belong to the plan's event."})
        is_calibration_project = plan.calibration_projects.filter(id=self.project_id).exists()
        if self.is_calibration and not is_calibration_project:
            raise ValidationError({"project": "Not one of this plan's calibration projects."})
        if not self.is_calibration and is_calibration_project:
            raise ValidationError(
                {"project": "This project is reserved for calibration, not live judging."}
            )
        if plan.prize_judging:
            from .eligibility import eligible_projects

            if not PoolMembership.objects.filter(
                pool_id=plan.pool_id, judge_id=self.judge_id
            ).exists():
                raise ValidationError({"judge": "Judge is not in this prize judging pool."})
            if (
                not self.is_calibration
                and not eligible_projects(plan).filter(id=self.project_id).exists()
            ):
                raise ValidationError({"project": "Project is not eligible for this prize."})


class BallotDraft(PublicIdModel):
    """A judge's in-progress, autosaved ballot (JUX-002). Deliberately kept
    separate from the immutable `Ballot`/`BallotResponse` pair rather than
    adding draft/submitted states to those models: a draft can be partial,
    invalid, or abandoned entirely, none of which should ever be able to
    touch the submitted-evidence tables. Submitting deletes the draft.
    """

    plan = models.ForeignKey(EvaluationPlan, on_delete=models.CASCADE, related_name="ballot_drafts")
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ballot_drafts"
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="ballot_drafts")
    responses = models.JSONField(default=dict, blank=True)  # {criterion_id: score}, may be partial
    comment = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["plan", "judge", "project"], name="unique_ballot_draft")
        ]


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


class EvaluationPool(PublicIdModel):
    """A named roster of judges an EvaluationPlan draws from (JDG-005)."""

    event = models.ForeignKey(
        "events.Event", on_delete=models.CASCADE, related_name="evaluation_pools"
    )
    name = models.CharField(max_length=160)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "name"], name="unique_evaluation_pool_name")
        ]


class PoolMembership(PublicIdModel):
    """One judge's membership in a pool, with the tracks they're expert in.

    Track-fit is a real scoring factor in `assignment.compute_assignment`,
    but nothing upstream (Project/Team) records which track a candidate
    belongs to yet, so it currently never discriminates -- see JDG-007's
    docstring and the C-B14 batch report.
    """

    pool = models.ForeignKey(EvaluationPool, on_delete=models.CASCADE, related_name="memberships")
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pool_memberships"
    )
    track_expertise = models.ManyToManyField(Track, blank=True, related_name="expert_judges")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["pool", "judge"], name="unique_pool_membership")
        ]

    def clean(self):
        workspace = self.pool.event.workspace
        if not has_any_role(self.judge, workspace, Role.JUDGE):
            raise ValidationError({"judge": "User must hold the judge role in this workspace."})


class ConflictOfInterest(PublicIdModel):
    """A judge's declared (or organizer-recorded) recusal from one candidate
    (JDG-006). Hard-enforced: excluded from assignment and rejected outright
    if a ballot is attempted anyway (see evaluations.views).
    """

    event = models.ForeignKey(
        "events.Event", on_delete=models.CASCADE, related_name="conflicts_of_interest"
    )
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="declared_conflicts"
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="judge_conflicts")
    reason = models.TextField(blank=True)
    declared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="conflicts_declared"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["judge", "project"], name="unique_conflict_of_interest")
        ]

    def clean(self):
        if self.project.event_id != self.event_id:
            raise ValidationError({"project": "Project must belong to the declared event."})


class AssignmentVersion(PublicIdModel):
    """One immutable, computed assignment run (JDG-008): freezes exactly
    which judge reviews which candidate, and why (evidence), the same way
    RubricVersion freezes a rubric.
    """

    plan = models.ForeignKey(
        EvaluationPlan, on_delete=models.PROTECT, related_name="assignment_versions"
    )
    number = models.PositiveIntegerField()
    coverage = models.PositiveIntegerField()
    evidence = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["plan", "number"], name="unique_assignment_version")
        ]
        ordering = ["number"]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Activated assignment versions are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Activated assignment versions are immutable.")


class Assignment(PublicIdModel):
    version = models.ForeignKey(
        AssignmentVersion, on_delete=models.CASCADE, related_name="assignments"
    )
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignments"
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="assignments")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["version", "judge", "project"], name="unique_assignment"
            )
        ]


class NormalizationRun(PublicIdModel):
    """One immutable, computed judge-effect estimation (NORM-004): the
    raw->adjusted->final trace lives entirely in `evidence`, computed once
    and frozen -- rerunning normalization creates a new numbered run rather
    than mutating this one, the same pattern as RubricVersion/
    AssignmentVersion.
    """

    plan = models.ForeignKey(
        EvaluationPlan, on_delete=models.PROTECT, related_name="normalization_runs"
    )
    number = models.PositiveIntegerField()
    ridge_lambda = models.FloatField()
    iterations = models.PositiveIntegerField()
    converged = models.BooleanField()
    grand_mean = models.FloatField()
    evidence = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["plan", "number"], name="unique_normalization_run")
        ]
        ordering = ["number"]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Normalization runs are immutable once computed.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Normalization runs are immutable once computed.")


class PairwiseComparison(PublicIdModel):
    """One judge's head-to-head verdict between two candidates (S01):
    holistic comparison judging as an alternative to per-criterion rubric
    scoring for a `PAIRWISE`-mode EvaluationPlan, aggregated via the
    Bradley-Terry model (see evaluations/pairwise.py). `project_a`/
    `project_b` are always stored with `project_a_id < project_b_id` (see
    `clean`), so a (plan, judge, project_a, project_b) tuple is unique
    regardless of which order the judge was shown the two candidates in;
    `winner` is null for a declared tie.
    """

    plan = models.ForeignKey(
        EvaluationPlan, on_delete=models.CASCADE, related_name="pairwise_comparisons"
    )
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pairwise_comparisons"
    )
    project_a = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="pairwise_as_a")
    project_b = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="pairwise_as_b")
    winner = models.ForeignKey(
        Project, null=True, blank=True, on_delete=models.PROTECT, related_name="pairwise_wins"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "judge", "project_a", "project_b"],
                name="unique_pairwise_comparison",
            ),
            models.CheckConstraint(
                condition=models.Q(project_a__lt=models.F("project_b")),
                name="pairwise_comparison_canonical_order",
            ),
        ]

    def clean(self):
        if self.plan.mode != EvaluationMode.PAIRWISE:
            raise ValidationError({"plan": "Plan is not configured for pairwise judging."})
        if self.plan.prize_judging:
            from .eligibility import eligible_projects

            if not PoolMembership.objects.filter(
                pool_id=self.plan.pool_id, judge_id=self.judge_id
            ).exists():
                raise ValidationError({"judge": "Judge is not in this prize judging pool."})
            eligible = set(
                eligible_projects(self.plan)
                .filter(id__in=(self.project_a_id, self.project_b_id))
                .values_list("id", flat=True)
            )
            if eligible != {self.project_a_id, self.project_b_id}:
                raise ValidationError(
                    {"project_a": "Both projects must be eligible for this prize."}
                )
        if self.project_a_id == self.project_b_id:
            raise ValidationError({"project_b": "A comparison needs two distinct candidates."})
        if self.project_a_id > self.project_b_id:
            self.project_a, self.project_b = self.project_b, self.project_a
        event_id = self.plan.stage.event_id
        if self.project_a.event_id != event_id or self.project_b.event_id != event_id:
            raise ValidationError({"project_a": "Both candidates must belong to the plan's event."})
        if self.winner_id is not None and self.winner_id not in (
            self.project_a_id,
            self.project_b_id,
        ):
            raise ValidationError({"winner": "Winner must be one of the two compared candidates."})


class PairwiseRun(PublicIdModel):
    """One immutable, computed Bradley-Terry strength estimation for a
    PAIRWISE-mode plan's comparisons (S01), the pairwise analogue of
    NormalizationRun -- see evaluations/pairwise.py::run. Rerunning creates
    a new numbered run rather than mutating a previous one.
    """

    plan = models.ForeignKey(EvaluationPlan, on_delete=models.PROTECT, related_name="pairwise_runs")
    number = models.PositiveIntegerField()
    prior_games = models.FloatField()
    iterations = models.PositiveIntegerField()
    converged = models.BooleanField()
    evidence = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["plan", "number"], name="unique_pairwise_run")
        ]
        ordering = ["number"]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Pairwise runs are immutable once computed.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Pairwise runs are immutable once computed.")
