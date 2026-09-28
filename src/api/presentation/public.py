"""Data access for the public, server-rendered site (GAL-001/GAL-002).

Every view here is unauthenticated and must show real content in the raw
HTTP response with no JS execution, so these return plain querysets/dicts a
Django template renders directly -- no client-side fetch involved.
"""

from artifacts.models import Artifact, ArtifactStatus, ArtifactVisibility
from artifacts.storage import S3Storage
from django.http import Http404
from django.shortcuts import get_object_or_404
from events.models import PUBLICLY_VISIBLE_STATUSES, Event, EventStatus
from projects.models import Project, SubmissionStatus

from .models import PublicationSurface
from .publication import publication_visible


def get_public_event(event_public_id):
    event = get_object_or_404(
        Event, public_id=event_public_id, is_public=True, status__in=PUBLICLY_VISIBLE_STATUSES
    )
    if event.status == EventStatus.ARCHIVED and not publication_visible(
        event, PublicationSurface.ARCHIVE
    ):
        raise Http404("Archive has not been released.")
    return event


def public_projects(event, *, q=None, stage_public_id=None, track_public_id=None):
    """Finalized projects the team has not hidden and no organizer has blocked."""
    if not publication_visible(event, PublicationSurface.GALLERY):
        return Project.objects.none()
    filters = {
        "event": event,
        "submissions__status": SubmissionStatus.FINALIZED,
        "gallery_visible": True,
        "gallery_blocked": False,
    }
    if stage_public_id:
        filters["submissions__stage__public_id"] = stage_public_id
    projects = (
        Project.objects.filter(**filters)
        .select_related("team", "track")
        .distinct()
        .order_by("name")
    )
    if q:
        projects = projects.filter(name__icontains=q)
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
