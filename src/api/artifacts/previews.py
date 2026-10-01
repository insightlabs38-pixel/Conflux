"""Preview sources for submitted artifacts and job outputs (ARTIFACT_PREVIEW, PD-F002-B02-T03).

`core.previews` turns what a source knows into the one descriptor the browser draws; the sources
here only decide who may see a thing and hand over what is already known about it:

- `project_artifact` is the stored static inspection of a submitted artifact (the same rows the
  reviewer endpoints show) and the same visibility rules (`artifacts.access`).
- `job_output` is a background job's output. It is inspected on the fly with the same inspector,
  never stored, and visible to whoever may see the job (`core.jobs.visible_to`).
"""

import uuid

from core import jobs, previews
from django.urls import reverse
from events.models import Event
from projects.models import Project

from . import access
from .inspector import MAX_INSPECT_BYTES, inspect_bytes
from .models import ArtifactStatus
from .services import inspection_data
from .storage import S3Storage


def _ids(ref, *names):
    try:
        return [uuid.UUID(ref[name]) for name in names]
    except (KeyError, ValueError, TypeError):
        return None


def project_artifact(user, workspace, ref):
    ids = _ids(ref, "event", "project", "artifact")
    if ids is None:
        return None
    event_id, project_id, artifact_id = ids
    event = Event.objects.filter(workspace=workspace, public_id=event_id).first()
    project = event and Project.objects.filter(event=event, public_id=project_id).first()
    if project is None:
        return None
    scope = access.reviewer_scope(user, workspace, project)
    artifact = scope and project.artifacts.filter(public_id=artifact_id).first()
    if not artifact or not access.visible(artifact, scope):
        return None
    latest = artifact.inspections.first()
    subject = previews.Subject(
        name=artifact.title,
        content_type=artifact.content_type,
        size=artifact.byte_size,
        kind_hint=artifact.kind,
        external_url=artifact.external_url,
        inspection=inspection_data(latest) if latest else None,
    )
    if artifact.status == ArtifactStatus.PURGED:
        subject.unavailable = ("purged", "This file's content was purged by retention policy.")
    elif (
        artifact.object_key
        and artifact.status == ArtifactStatus.READY
        and (latest is None or latest.verdict != "blocked")
    ):
        subject.download_url = S3Storage().presign_get(
            artifact.object_key, download_filename=artifact.title
        )
    return subject


def job_output(user, workspace, ref):
    ids = _ids(ref, "job")
    name = ref.get("name") if isinstance(ref.get("name"), str) else None
    if ids is None or not name:
        return None
    job = jobs.visible_to(user, workspace).filter(public_id=ids[0]).first()
    output = job and job.artifacts.filter(name=name).first()
    if output is None:
        return None
    subject = previews.Subject(
        name=output.name,
        content_type=output.content_type,
        size=output.size,
        download_url=reverse(
            "job-artifact",
            kwargs={
                "workspace_public_id": workspace.public_id,
                "job_public_id": job.public_id,
                "artifact_name": output.name,
            },
        ),
    )
    if output.size > MAX_INSPECT_BYTES:
        subject.unavailable = ("too_large", "This output is too large to preview; download it.")
    else:
        report = inspect_bytes(
            bytes(output.body),
            claimed_type=output.content_type,
            filename=output.name,
            kind="file",
        )
        subject.inspection = report.as_dict()
    return subject


def register():
    previews.register_source(
        previews.PreviewSource(
            "project_artifact",
            "Submitted artifact",
            params=("event", "project", "artifact"),
            resolve=project_artifact,
        )
    )
    previews.register_source(
        previews.PreviewSource(
            "job_output", "Job output", params=("job", "name"), resolve=job_output
        )
    )
