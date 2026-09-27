from core.models import PublicIdModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from events.models import BasePrize, Event, Track


class SelectionSource(models.TextChoices):
    MANUAL = "manual", "Manual"
    EVALUATION = "evaluation", "Evaluation results"
    COMMUNITY = "community", "Community vote"


class Award(PublicIdModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="awards")
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    eligibility_track = models.ForeignKey(
        Track, null=True, blank=True, on_delete=models.PROTECT, related_name="awards"
    )
    require_finalized_submission = models.BooleanField(default=True)
    selection_source = models.CharField(
        max_length=20, choices=SelectionSource.choices, default=SelectionSource.MANUAL
    )
    evaluation_plan = models.ForeignKey(
        "evaluations.EvaluationPlan", null=True, blank=True, on_delete=models.PROTECT
    )
    winner_count = models.PositiveSmallIntegerField(default=1)
    allow_stacking = models.BooleanField(default=True)
    conflict_group = models.CharField(max_length=80, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # VS19: which sponsor(s) can see this award's eligible projects/judges
    # and advance its fulfillments through the sponsor portal -- organizer-
    # managed, additive to (never a substitute for) organizer/admin access.
    sponsor_contacts = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="sponsored_awards"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "name"], name="unique_award_name_event"),
            models.CheckConstraint(
                condition=models.Q(winner_count__gte=1), name="award_winner_count_positive"
            ),
        ]

    def clean(self):
        errors = {}
        if self.eligibility_track_id and self.eligibility_track.event_id != self.event_id:
            errors["eligibility_track"] = "Track must belong to the award event."
        if self.selection_source == SelectionSource.EVALUATION:
            if not self.evaluation_plan_id:
                errors["evaluation_plan"] = "Evaluation selection requires a plan."
            elif self.evaluation_plan.stage.event_id != self.event_id:
                errors["evaluation_plan"] = "Plan must belong to the award event."
            elif self.evaluation_plan.prize_judging:
                if (
                    Award.objects.filter(evaluation_plan_id=self.evaluation_plan_id)
                    .exclude(pk=self.pk)
                    .exists()
                ):
                    errors["evaluation_plan"] = "A prize judging plan can serve only one award."
                elif (
                    self.evaluation_plan.assignment_versions.exists()
                    or self.evaluation_plan.rubric_versions.filter(ballots__isnull=False).exists()
                    or self.evaluation_plan.pairwise_comparisons.exists()
                ):
                    errors["evaluation_plan"] = "Link the award before judging begins."
        elif self.evaluation_plan_id:
            errors["evaluation_plan"] = "Only evaluation selection can reference a plan."
        if self.winner_count < 1:
            errors["winner_count"] = "Winner count must be positive."
        if errors:
            raise ValidationError(errors)


class PrizePackage(PublicIdModel):
    award = models.OneToOneField(Award, on_delete=models.CASCADE, related_name="prize_package")
    name = models.CharField(max_length=160)


class PrizeComponent(PublicIdModel):
    package = models.ForeignKey(PrizePackage, on_delete=models.CASCADE, related_name="components")
    kind = models.CharField(max_length=20, choices=BasePrize.Kind.choices)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    quantity = models.PositiveSmallIntegerField(default=1)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1), name="prize_quantity_positive"
            )
        ]

    def clean(self):
        errors = {}
        if self.quantity < 1:
            errors["quantity"] = "Quantity must be positive."
        if self.kind == BasePrize.Kind.CASH:
            if self.amount is None or self.amount <= 0:
                errors["amount"] = "Cash requires a positive amount."
            if len(self.currency) != 3 or not self.currency.isalpha():
                errors["currency"] = "Cash requires a three-letter currency."
        elif self.amount is not None or self.currency:
            errors["amount"] = "Only cash components can carry an amount and currency."
        if errors:
            raise ValidationError(errors)


class AwardWinner(PublicIdModel):
    award = models.ForeignKey(Award, on_delete=models.CASCADE, related_name="winners")
    project = models.ForeignKey(
        "projects.Project", on_delete=models.PROTECT, related_name="award_wins"
    )
    selected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    source = models.CharField(max_length=20, choices=SelectionSource.choices)
    evidence = models.JSONField(default=dict)
    override_reason = models.TextField(blank=True)
    selected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["award", "project"], name="unique_award_project_winner")
        ]


class FulfillmentState(models.TextChoices):
    PENDING = "pending", "Pending"
    CONTACTED = "contacted", "Contacted"
    VERIFIED = "verified", "Verified"
    SENT = "sent", "Sent"
    CLAIMED = "claimed", "Claimed"
    FAILED = "failed", "Failed"


class PrizeFulfillment(PublicIdModel):
    winner = models.ForeignKey(AwardWinner, on_delete=models.CASCADE, related_name="fulfillments")
    component = models.ForeignKey(
        PrizeComponent, on_delete=models.PROTECT, related_name="fulfillments"
    )
    state = models.CharField(
        max_length=12, choices=FulfillmentState.choices, default=FulfillmentState.PENDING
    )
    note = models.TextField(blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["winner", "component"], name="unique_winner_component_fulfillment"
            )
        ]

    def clean(self):
        if (
            self.component_id
            and self.winner_id
            and self.component.package.award_id != self.winner.award_id
        ):
            raise ValidationError({"component": "Component must belong to the winner's award."})
