import secrets
from datetime import timedelta

from botocore.exceptions import ClientError
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import STORED_KINDS, Artifact, ArtifactStatus, ArtifactUploadIntent
from .storage import MAX_PARTS, MULTIPART_THRESHOLD, PART_SIZE, S3Storage

MAX_UPLOAD_BYTES = MAX_PARTS * PART_SIZE


def _require_project_member(project, user):
    if not project.memberships.filter(user=user).exists():
        raise ValidationError("Only project members can manage its artifacts.")


def _expires_at(event):
    now = timezone.now()
    end = now + timedelta(minutes=15)
    if event.ends_at:
        end = min(end, event.ends_at)
    if end <= now:
        raise ValidationError("The event upload window has closed.")
    return end


@transaction.atomic
def create_external_artifact(project, actor, *, kind, visibility, title, url):
    _require_project_member(project, actor)
    artifact = Artifact(
        project=project,
        created_by=actor,
        kind=kind,
        visibility=visibility,
        title=title,
        external_url=url,
        status=ArtifactStatus.UPLOADED,
    )
    artifact.full_clean()
    artifact.save()
    return artifact


@transaction.atomic
def begin_upload(project, actor, *, kind, visibility, title, byte_size, content_type, storage=None):
    _require_project_member(project, actor)
    if kind not in STORED_KINDS:
        raise ValidationError("This artifact kind uses an external URL.")
    if (
        not isinstance(byte_size, int)
        or isinstance(byte_size, bool)
        or byte_size < 0
        or byte_size > MAX_UPLOAD_BYTES
    ):
        raise ValidationError("Upload size is outside the supported range.")
    if not isinstance(content_type, str) or not content_type or len(content_type) > 200:
        raise ValidationError("A content type is required.")
    expires_at = _expires_at(project.event)
    artifact = Artifact(
        project=project,
        created_by=actor,
        kind=kind,
        visibility=visibility,
        title=title,
        content_type=content_type,
    )
    artifact.full_clean()
    storage = storage or S3Storage()
    storage.ensure_bucket()
    artifact.save()
    key = (
        f"events/{project.event.public_id}/projects/{project.public_id}/"
        f"artifacts/{artifact.public_id}/{secrets.token_hex(12)}"
    )
    seconds = max(1, int((expires_at - timezone.now()).total_seconds()))
    if byte_size >= MULTIPART_THRESHOLD:
        upload_id, urls = storage.start_multipart(
            key, content_type, str(artifact.public_id), byte_size, seconds
        )
        intent = ArtifactUploadIntent(
            artifact=artifact,
            object_key=key,
            expected_size=byte_size,
            expected_type=content_type,
            upload_id=upload_id,
            part_count=len(urls),
            expires_at=expires_at,
        )
        intent.save()
        return artifact, intent, {"mode": "multipart", "part_size": PART_SIZE, "urls": urls}
    url = storage.presign_put(key, content_type, str(artifact.public_id), seconds)
    intent = ArtifactUploadIntent(
        artifact=artifact,
        object_key=key,
        expected_size=byte_size,
        expected_type=content_type,
        expires_at=expires_at,
    )
    intent.save()
    return (
        artifact,
        intent,
        {
            "mode": "single",
            "url": url,
            "headers": {
                "Content-Type": content_type,
                "x-amz-meta-artifact-id": str(artifact.public_id),
            },
        },
    )


@transaction.atomic
def complete_upload(intent, actor, *, parts=None, storage=None):
    intent = (
        ArtifactUploadIntent.objects.select_for_update(of=("self",))
        .select_related("artifact__project")
        .get(pk=intent.pk)
    )
    _require_project_member(intent.artifact.project, actor)
    if not intent.is_active:
        raise ValidationError("Upload intent has expired or already completed.")
    storage = storage or S3Storage()
    if intent.upload_id:
        if (
            not isinstance(parts, list)
            or len(parts) != intent.part_count
            or any(
                not isinstance(part, dict)
                or part.get("PartNumber") != index
                or not isinstance(part.get("ETag"), str)
                or not part["ETag"]
                for index, part in enumerate(parts, 1)
            )
        ):
            raise ValidationError("Multipart completion needs every numbered part and ETag.")
        try:
            storage.complete_multipart(intent.object_key, intent.upload_id, parts)
        except ClientError as exc:
            # Completion can succeed in S3 before its response or DB commit is
            # lost. Only a matching HEAD below can confirm that recovery.
            if exc.response.get("Error", {}).get("Code") != "NoSuchUpload":
                raise
    elif parts:
        raise ValidationError("Single-part uploads do not accept multipart parts.")
    try:
        head = storage.head(intent.object_key)
    except Exception as exc:
        raise ValidationError("Uploaded object was not found in storage.") from exc
    if (
        head.get("ContentLength") != intent.expected_size
        or head.get("ContentType") != intent.expected_type
        or head.get("Metadata", {}).get("artifact-id") != str(intent.artifact.public_id)
    ):
        raise ValidationError("Uploaded object metadata does not match the intent.")
    artifact = intent.artifact
    artifact.object_key = intent.object_key
    artifact.byte_size = intent.expected_size
    artifact.status = ArtifactStatus.UPLOADED
    artifact.save(update_fields=["object_key", "byte_size", "status", "updated_at"])
    intent.completed_at = timezone.now()
    intent.save(update_fields=["completed_at"])
    return artifact
