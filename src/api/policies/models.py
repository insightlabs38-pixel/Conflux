from core.models import PublicIdModel
from django.core.exceptions import ValidationError
from django.db import models
from events.models import Event

from .evaluator import PolicyError, validate_structure


class Action(models.TextChoices):
    """The domain actions a policy can gate. Not exhaustive of everything
    the product does — only the ones later batches actually need to gate
    (submission, team join, stage advancement, community voting, awarding).
    """

    SUBMIT = "submit", "Submit"
    JOIN = "join", "Join"
    ADVANCE = "advance", "Advance"
    VOTE = "vote", "Vote"
    AWARD = "award", "Award"


class Policy(PublicIdModel):
    """A named, reusable policy AST scoped to one event. The AST itself is
    validated for shape at save time (POL-001's validate_structure); it
    can't be checked against real facts until it's actually evaluated for
    a specific action call, since the available facts depend on the call
    site.
    """

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="policies")
    name = models.CharField(max_length=120)
    ast = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "name"], name="unique_policy_name_event")
        ]

    def __str__(self):
        return self.name

    def clean(self):
        try:
            validate_structure(self.ast)
        except PolicyError as exc:
            raise ValidationError({"ast": str(exc)}) from exc


class PolicyBinding(PublicIdModel):
    """Binds one Policy to one (event, action) pair. At most one binding
    per action per event — a second policy for the same action replaces
    the binding, it doesn't stack (no defined semantics for combining two
    policies' evidence would exist yet).
    """

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="policy_bindings")
    action = models.CharField(max_length=20, choices=Action.choices)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name="bindings")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "action"], name="unique_policy_binding_per_action"
            )
        ]

    def clean(self):
        if self.policy_id and self.policy.event_id != self.event_id:
            raise ValidationError("A policy can only be bound within its own event.")
