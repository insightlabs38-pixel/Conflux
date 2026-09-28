import http.client
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
from .reachability import (
    GITHUB_REPO_PATH,
    GITLAB_REPO_PATH,
    github_evidence,
    gitlab_evidence,
    pinned_get,
)
from .storage import S3Storage

SUBMISSION_CI_VALIDATOR = "submission_ci"
SUBMISSION_CI_KINDS = {ArtifactKind.REPOSITORY, ArtifactKind.LIVE_URL}

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
        if current.status == ArtifactStatus.PURGED:
            result = ValidationResult(
                "artifact_state", "retry", "Artifact content was purged by retention policy."
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


def inspect_submission_ci(artifact) -> ValidationResult:
    """Real reachability (and, for a public GitHub repository, license +
    latest-commit) evidence for one `repository`/`live_url` artifact
    (S07). Never touches `artifact.status` -- this is supplementary
    evidence for an organizer to review, not a gate on artifact validity
    (a demo site being briefly down shouldn't destroy a team's submission).
    """
    from integrations.webhooks import validate_destination

    try:
        parts, address = validate_destination(artifact.external_url)
    except ValueError as exc:
        return ValidationResult(SUBMISSION_CI_VALIDATOR, "blocked", f"Unreachable link: {exc}")

    path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
    try:
        status = pinned_get(parts.hostname, address, path)
    except (OSError, TimeoutError, http.client.HTTPException) as exc:
        return ValidationResult(
            SUBMISSION_CI_VALIDATOR, "retry", f"Could not reach link: {exc}"[:500]
        )

    if status >= 400:
        return ValidationResult(
            SUBMISSION_CI_VALIDATOR, "warning", f"Link responded with HTTP {status}."[:500]
        )

    detail = f"Reachable (HTTP {status})."
    if artifact.kind == ArtifactKind.REPOSITORY and parts.hostname == "github.com":
        match = GITHUB_REPO_PATH.match(parts.path or "")
        if match:
            detail += " " + github_evidence(match["owner"], match["repo"])
    elif artifact.kind == ArtifactKind.REPOSITORY and parts.hostname == "gitlab.com":
        match = GITLAB_REPO_PATH.match(parts.path or "")
        if match:
            detail += " " + gitlab_evidence(match["owner"], match["repo"])
    return ValidationResult(SUBMISSION_CI_VALIDATOR, "ok", detail[:500])


def run_submission_ci(artifact) -> ArtifactValidation | None:
    """Compute + record one `inspect_submission_ci` evidence row. Returns
    None for a kind this check doesn't apply to (stored files, external
    video -- only repository/live_url are "advanced submission CI" here).
    """
    if artifact.kind not in SUBMISSION_CI_KINDS:
        return None
    result = inspect_submission_ci(artifact)
    return ArtifactValidation.objects.create(
        artifact=artifact, validator=result.validator, outcome=result.outcome, detail=result.detail
    )
