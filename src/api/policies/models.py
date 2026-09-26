from core.models import PublicIdModel
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
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


class TemporalGate(PublicIdModel):
    """A named open/close window, independent of the stage graph (a stage
    is "where you are"; a gate is "is this window open right now"). Server
    time is authoritative: `is_open`/`status` default to `timezone.now()`
    and never take a client-supplied clock. `opens_at`/`closes_at` persist
    as UTC (Django's USE_TZ=True guarantees this regardless of the input's
    timezone); any DST/local-time handling belongs entirely in the
    presentation layer, never here.
    """

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="temporal_gates")
    name = models.CharField(max_length=120)
    opens_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "name"], name="unique_gate_name_event")
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if self.opens_at and self.closes_at and self.opens_at >= self.closes_at:
            raise ValidationError({"closes_at": "A gate must close after it opens."})

    def status(self, at=None):
        now = at or timezone.now()
        if self.opens_at and now < self.opens_at:
            return "not_yet_open"
        if self.closes_at and now >= self.closes_at:
            return "closed"
        return "open"

    def is_open(self, at=None):
        return self.status(at) == "open"


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
