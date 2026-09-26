from core.models import PublicIdModel
from django.core.exceptions import ValidationError
from django.db import models
from events.models import Event


class Stage(PublicIdModel):
    """One node in an event's advancement graph. Advancement strategy (ST-003)
    and stage-specific participation rules (ST-004) attach here once built;
    this model only carries the graph shape and identity.
    """

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="stages")
    name = models.CharField(max_length=120)
    position = models.PositiveIntegerField(default=0)
    is_initial = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "name"], name="unique_stage_name_event")
        ]
        ordering = ["position", "id"]

    def __str__(self):
        return self.name

    def reaches(self, target):
        """True if `target` is reachable from this stage by following
        outgoing transitions (BFS). Used to reject an edge that would close
        a cycle before it's ever persisted.
        """
        seen = {self.pk}
        frontier = [self.pk]
        while frontier:
            next_frontier = []
            for stage_id in StageTransition.objects.filter(from_stage_id__in=frontier).values_list(
                "to_stage_id", flat=True
            ):
                if stage_id == target.pk:
                    return True
                if stage_id not in seen:
                    seen.add(stage_id)
                    next_frontier.append(stage_id)
            frontier = next_frontier
        return False


class StageTransition(PublicIdModel):
    """A directed edge in the stage graph. Multiple outgoing edges from one
    stage are a branch; multiple incoming edges to one stage are a merge —
    both are ordinary graph shapes here, not special-cased.
    """

    from_stage = models.ForeignKey(
        Stage, on_delete=models.CASCADE, related_name="outgoing_transitions"
    )
    to_stage = models.ForeignKey(
        Stage, on_delete=models.CASCADE, related_name="incoming_transitions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["from_stage", "to_stage"], name="unique_stage_transition"
            )
        ]

    def __str__(self):
        return f"{self.from_stage_id}->{self.to_stage_id}"

    def clean(self):
        if self.from_stage_id == self.to_stage_id:
            raise ValidationError("A stage cannot transition to itself.")
        if self.from_stage.event_id != self.to_stage.event_id:
            raise ValidationError("A transition must connect stages in the same event.")
        # Adding from->to would close a cycle exactly when `to` can already
        # reach `from` through some other path.
        if self.to_stage.reaches(self.from_stage):
            raise ValidationError("This transition would create a cycle in the stage graph.")


class StageEntry(PublicIdModel):
    """One subject's (team, project, or whatever a later batch scopes
    participation to) presence in a stage. `subject_type`/`subject_id`
    follow the same lightweight reference pattern as AuditEvent's target,
    rather than a real FK: the subject's own model (teams/projects) doesn't
    exist yet at this point in the build (C-B07/C-B08 land later), and this
    lets stages stay independent of exactly which one it ends up being.
    """

    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name="entries")
    subject_type = models.CharField(max_length=100)
    subject_id = models.CharField(max_length=64)
    entered_at = models.DateTimeField(auto_now_add=True)
    exited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            # The participation boundary: a subject is only ever *currently*
            # in one stage at a time, across the whole graph.
            models.UniqueConstraint(
                fields=["subject_type", "subject_id"],
                condition=models.Q(exited_at__isnull=True),
                name="unique_active_stage_entry_per_subject",
            )
        ]

    def __str__(self):
        return f"{self.subject_type}:{self.subject_id}@{self.stage_id}"
