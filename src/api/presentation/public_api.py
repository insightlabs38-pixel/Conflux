"""EMB-001's data source: a dependency-light JSON read of the public gallery,
for the embeddable Web Component (src/embed) or any other external
consumer. The server-rendered HTML gallery (site_views.gallery) stays the
checker-facing surface per DECISIONS.md X011; this is an additive API next
to it, not a replacement.
"""

from core.pagination import page_params, paged_response
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .public import get_public_event, public_projects


class GalleryItemOutput(serializers.Serializer):
    public_id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    track = serializers.CharField(allow_null=True)
    team = serializers.CharField(allow_null=True)
    url = serializers.CharField()


class PublicGalleryView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter("q", str),
            OpenApiParameter("limit", int, description="Page size, 1-100 (default 50)."),
            OpenApiParameter("offset", int, description="Rows to skip (default 0)."),
        ],
        responses=GalleryItemOutput(many=True),
    )
    def get(self, request, event_public_id):
        event = get_public_event(event_public_id)
        q = request.query_params.get("q", "").strip()
        limit, offset = page_params(request)
        projects = public_projects(event, q=q or None)
        return paged_response(
            request,
            projects,
            lambda page: gallery_items(request, event, page),
            limit=limit,
            offset=offset,
        )


def gallery_items(request, event, projects):
    return [
        {
            "public_id": str(project.public_id),
            "name": project.name,
            "description": project.description,
            "track": project.track.name if project.track else None,
            "team": project.team.name if project.team else None,
            "url": request.build_absolute_uri(
                f"/e/{event.public_id}/projects/{project.public_id}/"
            ),
        }
        for project in projects
    ]
