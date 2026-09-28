import hashlib
from tempfile import TemporaryFile

from botocore.exceptions import ClientError

from .models import STORED_KINDS, Artifact


def _metadata_matches(info, size, content_type, metadata):
    return (
        info.get("ContentLength") == size
        and info.get("ContentType") == content_type
        and info.get("Metadata", {}) == metadata
    )


def _read(store, key, *, output=None):
    response = store.get(key)
    digest = hashlib.sha256()
    size = 0
    body = response["Body"]
    try:
        while chunk := body.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
            if output is not None:
                output.write(chunk)
    finally:
        body.close()
    return response, size, digest.hexdigest()


def copy_event_artifacts(event, source, destination, *, execute=False):
    if (source.endpoint.rstrip("/"), source.bucket) == (
        destination.endpoint.rstrip("/"),
        destination.bucket,
    ):
        raise ValueError("Source and destination must be different storage namespaces")
    report = {"event": str(event.public_id), "executed": execute, "artifacts": []}
    artifacts = (
        Artifact.objects.filter(project__event=event, kind__in=STORED_KINDS)
        .exclude(object_key="")
        .select_related("project")
        .order_by("public_id")
    )
    bucket_ready = False
    for artifact in artifacts.iterator():
        key = artifact.object_key
        expected_prefix = (
            f"events/{event.public_id}/projects/{artifact.project.public_id}/"
            f"artifacts/{artifact.public_id}/"
        )
        if not key.startswith(expected_prefix) or not key.removeprefix(expected_prefix):
            raise ValueError(f"Artifact {artifact.public_id}: object key is outside its identity")
        with TemporaryFile() as spool:
            info, size, digest = _read(source, key, output=spool)
            metadata = info.get("Metadata", {})
            if (
                metadata.get("artifact-id") != str(artifact.public_id)
                or not _metadata_matches(info, artifact.byte_size, artifact.content_type, metadata)
                or size != artifact.byte_size
                or (artifact.sha256 and digest != artifact.sha256)
            ):
                raise ValueError(
                    f"Artifact {artifact.public_id}: source content or metadata mismatch"
                )
            try:
                existing = destination.head(key)
            except ClientError as exc:
                if exc.response.get("Error", {}).get("Code") not in {
                    "404",
                    "NoSuchKey",
                    "NotFound",
                    "NoSuchBucket",
                }:
                    raise
                existing = None
            if existing is not None:
                if not _metadata_matches(existing, size, artifact.content_type, metadata):
                    raise ValueError(
                        f"Artifact {artifact.public_id}: destination metadata collision"
                    )
                existing_info, existing_size, existing_digest = _read(destination, key)
                if not _metadata_matches(existing_info, size, artifact.content_type, metadata) or (
                    existing_size,
                    existing_digest,
                ) != (size, digest):
                    raise ValueError(
                        f"Artifact {artifact.public_id}: destination content collision"
                    )
                status = "verified_existing"
            elif execute:
                if not bucket_ready:
                    destination.ensure_bucket()
                    bucket_ready = True
                spool.seek(0)
                destination.put(
                    key,
                    spool,
                    content_type=artifact.content_type,
                    metadata=metadata,
                    only_if_absent=True,
                )
                copied_info, copied_size, copied_digest = _read(destination, key)
                if not _metadata_matches(copied_info, size, artifact.content_type, metadata) or (
                    copied_size,
                    copied_digest,
                ) != (size, digest):
                    raise ValueError(
                        f"Artifact {artifact.public_id}: destination verification failed"
                    )
                status = "copied"
            else:
                status = "would_copy"
            report["artifacts"].append(
                {
                    "artifact": str(artifact.public_id),
                    "object_key": key,
                    "bytes": size,
                    "sha256": digest,
                    "status": status,
                }
            )
    return report
