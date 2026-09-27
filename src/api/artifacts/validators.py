from dataclasses import dataclass

from botocore.exceptions import ClientError
from django.db import transaction

from .models import (
    EXTERNAL_KINDS,
    STORED_KINDS,
    Artifact,
    ArtifactKind,
    ArtifactStatus,
    ArtifactValidation,
)
from .storage import S3Storage

# Content types a browser will execute or actively render if ever served
# inline (GSEC-002): never acceptable for a stored artifact regardless of
# `kind`, `image/svg+xml` included -- SVG passes a naive "image/*" prefix
# check but can embed and run <script>. `storage.presign_get` already
# forces `Content-Disposition: attachment` for every download as the
# primary defense; this is the second, independent layer -- content this
# dangerous is rejected outright rather than trusted to stay undisplayed.
_ACTIVE_CONTENT_TYPES = {
    "text/html",
    "application/xhtml+xml",
    "image/svg+xml",
}


@dataclass(frozen=True)
class ValidationResult:
    validator: str
    outcome: str
    detail: str


def _stored_result(artifact, storage):
    try:
        head = storage.head(artifact.object_key)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code in {"404", "NoSuchKey", "NotFound"}:
            return ValidationResult("stored_object", "blocked", "Uploaded object is missing.")
        return ValidationResult("stored_object", "retry", "Storage could not verify the object.")
    except Exception:
        return ValidationResult("stored_object", "retry", "Storage could not verify the object.")
    if (
        head.get("ContentLength") != artifact.byte_size
        or head.get("ContentType") != artifact.content_type
        or head.get("Metadata", {}).get("artifact-id") != str(artifact.public_id)
    ):
        return ValidationResult(
            "stored_object", "blocked", "Stored object metadata does not match the artifact."
        )
    if artifact.content_type.split(";", 1)[0].strip().lower() in _ACTIVE_CONTENT_TYPES:
        return ValidationResult(
            "active_content_type",
            "blocked",
            "This media type can execute in a browser and is never accepted for evidence.",
        )
    if artifact.kind == ArtifactKind.IMAGE and not artifact.content_type.startswith("image/"):
        return ValidationResult(
            "image_media_type", "blocked", "Image evidence must use an image media type."
        )
    if artifact.kind == ArtifactKind.VIDEO and not artifact.content_type.startswith("video/"):
        return ValidationResult(
            "video_media_type", "blocked", "Video evidence must use a video media type."
        )
    return ValidationResult("stored_object", "ok", "Object metadata verified.")


def _external_result(artifact, storage):
    return ValidationResult(
        "external_link", "warning", "Link structure is valid; remote availability was not checked."
    )


VALIDATORS = {
    **{kind: _stored_result for kind in STORED_KINDS},
    **{kind: _external_result for kind in EXTERNAL_KINDS},
}


def inspect_artifact(artifact, *, storage=None):
    if artifact.status == ArtifactStatus.PENDING:
        return ValidationResult("upload_state", "retry", "Upload has not completed.")
    validator = VALIDATORS.get(artifact.kind)
    if validator is None:
        return ValidationResult("artifact_kind", "blocked", "Artifact kind is unsupported.")
    if artifact.kind in STORED_KINDS and (not artifact.object_key or artifact.byte_size is None):
        return ValidationResult("stored_object", "blocked", "Stored object metadata is incomplete.")
    storage_client = (storage or S3Storage()) if artifact.kind in STORED_KINDS else None
    return validator(artifact, storage_client)


def validate_artifact(artifact, *, storage=None):
    result = inspect_artifact(artifact, storage=storage)
    with transaction.atomic():
        current = Artifact.objects.select_for_update().get(pk=artifact.pk)
        if (
            current.updated_at != artifact.updated_at
            or current.object_key != artifact.object_key
            or current.status != artifact.status
        ):
            result = ValidationResult(
                "artifact_state", "retry", "Artifact changed during validation; retry."
            )
        evidence = ArtifactValidation.objects.create(
            artifact=current,
            validator=result.validator,
            outcome=result.outcome,
            detail=result.detail,
        )
        if result.outcome in {"ok", "warning"}:
            current.status = ArtifactStatus.READY
        elif result.outcome == "blocked":
            current.status = ArtifactStatus.REJECTED
        if result.outcome != "retry":
            current.save(update_fields=["status", "updated_at"])
    return evidence
