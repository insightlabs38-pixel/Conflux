from core.models import PublicIdModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from events.models import Event
from participation.models import Team


class Project(PublicIdModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="projects")
    team = models.ForeignKey(
        Team, null=True, blank=True, on_delete=models.SET_NULL, related_name="projects"
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
