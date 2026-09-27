from core.models import PublicIdModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.utils import timezone
from projects.models import Project


class ArtifactKind(models.TextChoices):
    FILE = "file", "File"
    IMAGE = "image", "Image"
    VIDEO = "video", "Video"
    EXTERNAL_VIDEO = "external_video", "External video"
    REPOSITORY = "repository", "Repository"
    LIVE_URL = "live_url", "Live URL"
    DOCUMENT = "document", "Technical document"
    DATASET = "dataset", "Dataset"
    SECRET = "secret", "Secret evidence"


class ArtifactVisibility(models.TextChoices):
    PUBLIC = "public", "Public"
    PARTICIPANT = "participant", "Participant"
    JUDGE = "judge", "Judge"
    ORGANIZER = "organizer", "Organizer"


class ArtifactStatus(models.TextChoices):
    PENDING = "pending", "Pending upload"
    UPLOADED = "uploaded", "Uploaded"
    READY = "ready", "Ready"
    REJECTED = "rejected", "Rejected"


EXTERNAL_KINDS = {ArtifactKind.EXTERNAL_VIDEO, ArtifactKind.REPOSITORY, ArtifactKind.LIVE_URL}
STORED_KINDS = {
    ArtifactKind.FILE,
    ArtifactKind.IMAGE,
    ArtifactKind.VIDEO,
    ArtifactKind.DOCUMENT,
    ArtifactKind.DATASET,
    ArtifactKind.SECRET,
}


class Artifact(PublicIdModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="artifacts")
    kind = models.CharField(max_length=20, choices=ArtifactKind.choices)
    visibility = models.CharField(max_length=20, choices=ArtifactVisibility.choices)
    title = models.CharField(max_length=200)
    external_url = models.URLField(blank=True)
    object_key = models.CharField(max_length=500, blank=True)
    content_type = models.CharField(max_length=200, blank=True)
    byte_size = models.PositiveBigIntegerField(null=True, blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    status = models.CharField(
        max_length=12, choices=ArtifactStatus.choices, default=ArtifactStatus.PENDING
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_artifacts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.kind in EXTERNAL_KINDS:
            if not self.external_url:
                raise ValidationError({"external_url": "A URL is required for this artifact kind."})
            URLValidator(schemes=["http", "https"])(self.external_url)
            if self.object_key:
                raise ValidationError(
                    {"object_key": "External artifacts cannot have stored objects."}
                )
        elif self.kind in STORED_KINDS:
            if self.external_url:
                raise ValidationError(
                    {"external_url": "Stored artifacts cannot use an external URL."}
                )
        if self.kind == ArtifactKind.SECRET and self.visibility not in {
            ArtifactVisibility.JUDGE,
            ArtifactVisibility.ORGANIZER,
        }:
            raise ValidationError(
                {"visibility": "Secret evidence must be judge or organizer visible."}
            )


def can_view_artifact(artifact, *, user=None, role=None):
    if artifact.visibility == ArtifactVisibility.PUBLIC:
        return True
    if user is None:
        return False
    if role in {"admin", "organizer"}:
        return True
    if artifact.visibility == ArtifactVisibility.JUDGE:
        return role == "judge"
    if artifact.visibility == ArtifactVisibility.PARTICIPANT:
        return artifact.project.memberships.filter(user=user).exists()
    return False


class ArtifactUploadIntent(PublicIdModel):
    artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE, related_name="upload_intents")
    object_key = models.CharField(max_length=500)
    expected_size = models.PositiveBigIntegerField()
    expected_type = models.CharField(max_length=200)
    upload_id = models.CharField(max_length=300, blank=True)
    part_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_active(self):
        return self.completed_at is None and timezone.now() < self.expires_at


class ArtifactValidation(PublicIdModel):
    class Outcome(models.TextChoices):
        OK = "ok", "OK"
        WARNING = "warning", "Warning"
        BLOCKED = "blocked", "Blocked"
        RETRY = "retry", "Retry"

    artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE, related_name="validations")
    validator = models.CharField(max_length=80)
    outcome = models.CharField(max_length=12, choices=Outcome.choices)
    detail = models.CharField(max_length=500)
    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-checked_at", "-id"]
