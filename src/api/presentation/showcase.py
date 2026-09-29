"""Read-only showcase hierarchy over the existing public visibility gates."""

from collections import defaultdict

from accounts.profile import identity_for
from artifacts.models import Artifact, ArtifactKind, ArtifactStatus, ArtifactVisibility
from django.db.models import Prefetch, prefetch_related_objects
from django.utils.html import strip_tags

from .public import public_artifact_view
from .technical import render_technical_description

RASTER_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
VIDEO_TYPES = {"video/mp4", "video/webm"}


def initials(name):
    return "".join(part[0] for part in name.split()[:2]).upper() or "?"


def prepare_showcase(projects, event):
    projects = list(projects)
    if not projects:
        return projects
    prefetch_related_objects(
        projects,
        "search_tags",
        "memberships__user__profile",
        "team__memberships__user__profile",
        "created_by__profile",
        Prefetch(
            "artifacts",
            queryset=Artifact.objects.filter(
                visibility=ArtifactVisibility.PUBLIC, status=ArtifactStatus.READY
            ).order_by("title", "public_id"),
            to_attr="public_showcase_artifacts",
        ),
    )
    from .stories import visible_awards

    awards = defaultdict(list)
    ids = {project.pk for project in projects}
    for award in visible_awards(event).filter(winners__project__in=projects).distinct():
        for winner in award.public_winners:
            if winner.project_id in ids:
                awards[winner.project_id].append({"name": award.name, "public_id": award.public_id})
    for project in projects:
        people = []
        memberships = list(
            project.team.memberships.all() if project.team_id else project.memberships.all()
        )
        users = [row.user for row in memberships] or [project.created_by]
        for user in users:
            identity = identity_for(user)
            if identity["profile_url"]:
                identity["initials"] = initials(identity["display_name"])
                people.append(identity)
        artifacts = []
        for row in project.public_showcase_artifacts:
            artifact = public_artifact_view(row)
            content_type = row.content_type.split(";", 1)[0].strip().lower()
            # Native raster/video decoders only. Documents, submitted code,
            # SVG/HTML and external video links are never embedded or executed.
            artifact.update(
                {
                    "byte_size": row.byte_size,
                    "content_type": content_type,
                    "preview": "image"
                    if row.kind == ArtifactKind.IMAGE
                    and row.object_key
                    and content_type in RASTER_TYPES
                    else "video"
                    if row.kind == ArtifactKind.VIDEO
                    and row.object_key
                    and content_type in VIDEO_TYPES
                    else "",
                    "sha256": row.sha256,
                    "public_id": row.public_id,
                }
            )
            artifacts.append(artifact)
        summary = " ".join(
            strip_tags(render_technical_description(project.description[:1200])).split()
        )
        project.showcase = {
            "initials": initials(project.name),
            "summary": summary,
            "tags": [row.tag for row in project.search_tags.all()],
            "people": people,
            "private_people": len(users) - len(people),
            "awards": awards[project.pk],
            "artifacts": artifacts,
            "media": [item for item in artifacts if item["preview"]],
            "cover": next((item for item in artifacts if item["preview"] == "image"), None),
        }
    return projects
