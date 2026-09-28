from core.models import PublicIdModel
from django.conf import settings
from django.db import models


class RoomStatus(models.TextChoices):
    OPEN = "open", "Open"
    CLOSED = "closed", "Closed"
    FINALIZED = "finalized", "Finalized"


class Stance(models.TextChoices):
    ENDORSE = "endorse", "Endorse"
    OBJECT = "object", "Object"
    ABSTAIN = "abstain", "Abstain"


class DeliberationRoom(PublicIdModel):
    """Judges' post-scoring discussion for one award. Notes and stances are
    written by judges only, and a judge sees a project's discussion only after
    submitting their own evaluation of it, so the room can never leak or
    anchor an independent score.
    """

    award = models.OneToOneField(
        "awards.Award", on_delete=models.CASCADE, related_name="deliberation_room"
    )
    status = models.CharField(max_length=10, choices=RoomStatus.choices, default=RoomStatus.OPEN)
    quorum = models.PositiveSmallIntegerField()
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    finalization = models.JSONField(default=dict, blank=True)


class DeliberationNote(PublicIdModel):
    room = models.ForeignKey(DeliberationRoom, on_delete=models.CASCADE, related_name="notes")
    project = models.ForeignKey(
        "projects.Project", null=True, blank=True, on_delete=models.CASCADE, related_name="+"
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    body = models.CharField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]


class DeliberationStance(PublicIdModel):
    room = models.ForeignKey(DeliberationRoom, on_delete=models.CASCADE, related_name="stances")
    judge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="+")
    stance = models.CharField(max_length=10, choices=Stance.choices)
    rationale = models.CharField(max_length=500, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["project_id", "judge_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["room", "judge", "project"], name="one_stance_per_judge_project"
            )
        ]
