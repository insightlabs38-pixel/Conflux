from core.models import PublicIdModel
from django.conf import settings
from django.db import models


class Role(models.TextChoices):
    """Workspace-scoped roles. "visitor" is deliberately absent: it is the
    state of holding no Membership row at all, not a stored value.
    """

    PARTICIPANT = "participant", "Participant"
    JUDGE = "judge", "Judge"
    ORGANIZER = "organizer", "Organizer"
    ADMIN = "admin", "Admin"


class Workspace(PublicIdModel):
    """The tenant boundary: one organizer's account, able to host many
    events over time. Event (a later batch) scopes dates/tracks/prizes
    inside a Workspace.
    """

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Membership(PublicIdModel):
    """A (user, workspace, role) grant. A user can hold more than one role
    in the same workspace (e.g. organizer and judge), so this is a scoped
    many-to-many rather than a single role column on the user or workspace.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=Role.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "workspace", "role"], name="unique_user_workspace_role"
            )
        ]

    def __str__(self):
        return f"{self.user_id}@{self.workspace_id}:{self.role}"
