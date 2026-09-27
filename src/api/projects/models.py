from core.models import PublicIdModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from events.models import Event, Track
from participation.models import Team
from stages.models import Stage


class Project(PublicIdModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="projects")
    team = models.ForeignKey(
        Team, null=True, blank=True, on_delete=models.SET_NULL, related_name="projects"
    )
    track = models.ForeignKey(
        Track, null=True, blank=True, on_delete=models.SET_NULL, related_name="projects"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.team_id and self.team.event_id != self.event_id:
            raise ValidationError({"team": "Team must belong to the project's event."})
        if self.track_id and self.track.event_id != self.event_id:
            raise ValidationError({"track": "Track must belong to the project's event."})


class ProjectMembershipRole(models.TextChoices):
    OWNER = "owner", "Owner"
    CONTRIBUTOR = "contributor", "Contributor"


class ProjectMembership(PublicIdModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="project_memberships"
    )
    role = models.CharField(max_length=12, choices=ProjectMembershipRole.choices)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["project", "user"], name="unique_project_member")
        ]

    def clean(self):
        if not self.project.event.workspace.memberships.filter(user=self.user).exists():
            raise ValidationError({"user": "Project member must belong to the event workspace."})
        if (
            self.project.team_id
            and not self.project.team.memberships.filter(user=self.user).exists()
        ):
            raise ValidationError({"user": "Project member must belong to the project team."})


class SubmissionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    FINALIZED = "finalized", "Finalized"


class Submission(PublicIdModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="submissions")
    stage = models.ForeignKey(Stage, on_delete=models.PROTECT, related_name="submissions")
    status = models.CharField(
        max_length=12, choices=SubmissionStatus.choices, default=SubmissionStatus.DRAFT
    )
    draft_payload = models.JSONField(default=dict, blank=True)
    draft_revision = models.PositiveIntegerField(default=0)
    current_version = models.ForeignKey(
        "SubmissionVersion",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="current_for",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="submissions_updated"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "stage"], name="unique_project_stage_submission"
            )
        ]

    def clean(self):
        if self.stage.event_id != self.project.event_id:
            raise ValidationError("Submission stage must belong to the project's event.")
        if self.current_version_id and self.current_version.submission_id != self.pk:
            raise ValidationError("Current version must belong to this submission.")


class SubmissionVersion(PublicIdModel):
    submission = models.ForeignKey(Submission, on_delete=models.PROTECT, related_name="versions")
    number = models.PositiveIntegerField()
    snapshot = models.JSONField()
    digest = models.CharField(max_length=64)
    finalized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="finalized_submissions"
    )
    finalized_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "number"], name="unique_submission_version"
            )
        ]
        ordering = ["number"]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Finalized submission versions are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Finalized submission versions are immutable.")
