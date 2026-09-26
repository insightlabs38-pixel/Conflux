from core.models import PublicIdModel
from django.core.exceptions import ValidationError
from django.db import models
from events.models import Event


class ParticipationMode(models.TextChoices):
    """What kind of subject a stage's entries hold, and whether team
    composition is expected to still be changing there. Full team-locking
    (freezing membership on a real Team model) is C-B07's job once that
    model exists; this only carries the signal (`locks_team_membership`)
    and enforces the subject_type it implies (`StageEntryManager.enter`).
    """

    INDIVIDUAL = "individual", "Individual"
    TEAM_FORMATION = "team_formation", "Team formation"
    TEAM_LOCKED = "team_locked", "Team locked"


SUBJECT_TYPE_FOR_MODE = {
    ParticipationMode.INDIVIDUAL: "user",
    ParticipationMode.TEAM_FORMATION: "team",
    ParticipationMode.TEAM_LOCKED: "team",
}


class Stage(PublicIdModel):
    """One node in an event's advancement graph. Advancement strategy (ST-003)
    attaches here through `advance_stage`; this model carries the graph
    shape, identity, and (ST-004) what kind of subject may hold an entry.
    """

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="stages")
    name = models.CharField(max_length=120)
    position = models.PositiveIntegerField(default=0)
    is_initial = models.BooleanField(default=False)
    participation_mode = models.CharField(
        max_length=20,
        choices=ParticipationMode.choices,
        default=ParticipationMode.TEAM_FORMATION,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "name"], name="unique_stage_name_event")
        ]
        ordering = ["position", "id"]

    def __str__(self):
        return self.name

    def expected_subject_type(self):
        return SUBJECT_TYPE_FOR_MODE[self.participation_mode]

    @property
    def locks_team_membership(self):
        return self.participation_mode == ParticipationMode.TEAM_LOCKED

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


class StageEntryManager(models.Manager):
    def enter(self, stage, subject_type, subject_id):
        """The validated way to create a StageEntry: rejects a subject_type
        that doesn't match the stage's participation_mode (ST-004), e.g. a
        "team" trying to enter an individual-only stage. Direct
        `.create()` still works for tests/fixtures that don't care about
        this rule; real mutation paths (`advance_stage`) go through here.
        """
        expected = stage.expected_subject_type()
        if subject_type != expected:
            raise ValidationError(
                f"{stage.get_participation_mode_display()} stage {stage.name!r} requires "
                f"subject_type={expected!r}, got {subject_type!r}."
            )
        return self.create(stage=stage, subject_type=subject_type, subject_id=subject_id)


class StageEntry(PublicIdModel):
    """One subject's (team, project, or whatever a later batch scopes
    participation to) presence in a stage. `subject_type`/`subject_id`
    follow the same lightweight reference pattern as AuditEvent's target,
    rather than a real FK: the subject's own model (teams/projects) doesn't
    exist yet at this point in the build (C-B07/C-B08 land later), and this
    lets stages stay independent of exactly which one it ends up being.
    """

    objects = StageEntryManager()

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
