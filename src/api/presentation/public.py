"""Data access for the public, server-rendered site (GAL-001/GAL-002).

Every view here is unauthenticated and must show real content in the raw
HTTP response with no JS execution, so these return plain querysets/dicts a
Django template renders directly -- no client-side fetch involved.
"""

from artifacts.models import Artifact, ArtifactStatus, ArtifactVisibility
from artifacts.storage import S3Storage
from django.shortcuts import get_object_or_404
from events.models import Event, EventStatus
from projects.models import Project, SubmissionStatus


def get_public_event(event_public_id):
    return get_object_or_404(
        Event, public_id=event_public_id, is_public=True, status=EventStatus.OPEN
    )


def public_projects(event, *, q=None, stage_public_id=None, track_public_id=None):
    """Projects with at least one finalized submission for this event."""
    projects = (
        Project.objects.filter(event=event, submissions__status=SubmissionStatus.FINALIZED)
        .select_related("team", "track")
        .distinct()
        .order_by("name")
    )
    if q:
        projects = projects.filter(name__icontains=q)
    if stage_public_id:
        projects = projects.filter(submissions__stage__public_id=stage_public_id)
    if track_public_id:
        projects = projects.filter(track__public_id=track_public_id)
    return projects


def public_artifact_view(artifact):
    """A safe, presentational view of one PUBLIC artifact (never raw model)."""
    url = artifact.external_url
    if not url and artifact.object_key:
        url = S3Storage().presign_get(artifact.object_key, download_filename=artifact.title)
    return {"title": artifact.title, "kind": artifact.kind, "url": url}


def project_public_artifacts(project):
    return [
        public_artifact_view(artifact)
        for artifact in Artifact.objects.filter(
            project=project, visibility=ArtifactVisibility.PUBLIC, status=ArtifactStatus.READY
        ).order_by("title")
    ]


def project_finalized_submissions(project):
    return (
        project.submissions.filter(status=SubmissionStatus.FINALIZED)
        .select_related("stage", "current_version")
        .order_by("stage__position")
    )
