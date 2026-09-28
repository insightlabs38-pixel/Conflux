from core.models import PublicIdModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class EligibilityRules(PublicIdModel):
    """Objective, automatically checkable requirements. Everything else an
    organizer wants to check is raised by hand as a finding.
    """

    event = models.OneToOneField(
        "events.Event", on_delete=models.CASCADE, related_name="eligibility_rules"
    )
    min_team_size = models.PositiveSmallIntegerField(null=True, blank=True)
    max_team_size = models.PositiveSmallIntegerField(null=True, blank=True)
    required_artifact_kinds = models.JSONField(default=list, blank=True)
    require_finalized_submission = models.BooleanField(default=False)
    require_track = models.BooleanField(default=False)
    require_clearance = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        from artifacts.models import ArtifactKind

        if (
            self.min_team_size is not None
            and self.max_team_size is not None
            and self.min_team_size > self.max_team_size
        ):
            raise ValidationError({"max_team_size": "Maximum must not be below the minimum."})
        kinds = self.required_artifact_kinds
        if (
            not isinstance(kinds, list)
            or len(set(kinds)) != len(kinds)
            or any(kind not in ArtifactKind.values for kind in kinds)
        ):
            raise ValidationError({"required_artifact_kinds": "Use unique, known artifact kinds."})


class ReviewStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    NEEDS_REMEDIATION = "needs_remediation", "Needs remediation"
    CLEARED = "cleared", "Cleared"
    INELIGIBLE = "ineligible", "Ineligible"


class EligibilityReview(PublicIdModel):
    project = models.OneToOneField(
        "projects.Project", on_delete=models.CASCADE, related_name="eligibility_review"
    )
    status = models.CharField(
        max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    decision_note = models.CharField(max_length=1000, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    revision = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FindingSeverity(models.TextChoices):
    BLOCKING = "blocking", "Blocking"
    ADVISORY = "advisory", "Advisory"


class FindingState(models.TextChoices):
    OPEN = "open", "Open"
    ADDRESSED = "addressed", "Addressed by participant"
    RESOLVED = "resolved", "Resolved"
    WAIVED = "waived", "Waived"


class EligibilityFinding(PublicIdModel):
    review = models.ForeignKey(EligibilityReview, on_delete=models.CASCADE, related_name="findings")
    code = models.CharField(max_length=60)
    automated = models.BooleanField(default=False)
    severity = models.CharField(max_length=10, choices=FindingSeverity.choices)
    message = models.CharField(max_length=500)
    state = models.CharField(max_length=10, choices=FindingState.choices, default=FindingState.OPEN)
    participant_response = models.CharField(max_length=1000, blank=True)
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    resolution_note = models.CharField(max_length=500, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    addressed_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["opened_at", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["review", "code"],
                condition=Q(automated=True, state__in=["open", "addressed"]),
                name="one_live_automated_finding_per_code",
            )
        ]
