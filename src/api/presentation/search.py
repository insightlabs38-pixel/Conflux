from artifacts.models import Artifact, ArtifactKind, ArtifactStatus, ArtifactVisibility
from audit.services import record_mutation
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db import IntegrityError, connection, transaction
from django.db.models import Exists, OuterRef, Prefetch, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from events.models import Event, EventStatus
from projects.models import Project
from projects.views import ProjectView
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ProjectSearchTag, SavedPublicSearch
from .public import get_public_event, public_projects
from .public_api import GalleryItemOutput


class StrictSearchInput(serializers.Serializer):
    def to_internal_value(self, data):
        attrs = super().to_internal_value(data)
        if data.keys() - self.fields.keys():
            raise serializers.ValidationError({"non_field_errors": ["Unknown fields."]})
        return attrs


class SearchFilters(StrictSearchInput):
    q = serializers.CharField(max_length=200, required=False, allow_blank=True)
    tags = serializers.ListField(
        child=serializers.SlugField(max_length=30), max_length=10, required=False
    )
    artifact_kind = serializers.ChoiceField(choices=ArtifactKind.choices, required=False)
    track = serializers.UUIDField(required=False)
    stage = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if len(attrs.get("q", "").split()) > 10:
            raise serializers.ValidationError({"q": "Use at most 10 search terms."})
        if "tags" in attrs:
            attrs["tags"] = sorted({tag.lower() for tag in attrs["tags"]})
        return attrs


class SearchQueryInput(SearchFilters):
    offset = serializers.IntegerField(default=0, min_value=0, max_value=1000000)


class SearchItemOutput(GalleryItemOutput):
    tags = serializers.ListField(child=serializers.CharField())
    artifact_kinds = serializers.ListField(child=serializers.CharField())


class SearchOutput(serializers.Serializer):
    count = serializers.IntegerField()
    next_offset = serializers.IntegerField(allow_null=True)
    items = SearchItemOutput(many=True)


def search(event, filters, offset=0):
    projects = public_projects(
        event, stage_public_id=filters.get("stage"), track_public_id=filters.get("track")
    )
    q = filters.get("q", "").strip()
    if q:
        if connection.vendor == "postgresql":
            projects = projects.annotate(
                search_text=SearchVector("name", "description", config="simple")
            ).filter(search_text=SearchQuery(q, config="simple", search_type="plain"))
        else:
            for term in q.split():
                projects = projects.filter(Q(name__icontains=term) | Q(description__icontains=term))
    for tag in filters.get("tags", []):
        projects = projects.filter(search_tags__tag=tag)
    visible_artifacts = Artifact.objects.filter(
        visibility=ArtifactVisibility.PUBLIC, status=ArtifactStatus.READY
    )
    if filters.get("artifact_kind"):
        match = visible_artifacts.filter(project_id=OuterRef("pk"), kind=filters["artifact_kind"])
        projects = projects.annotate(has_artifact=Exists(match)).filter(has_artifact=True)
    projects = projects.order_by("name", "public_id")
    count = projects.count()
    rows = projects.prefetch_related(
        "search_tags", Prefetch("artifacts", queryset=visible_artifacts, to_attr="search_artifacts")
    )[offset : offset + 50]
    items = [
        {
            "public_id": str(project.public_id),
            "name": project.name,
            "description": project.description,
            "track": project.track.name if project.track else None,
            "team": project.team.name if project.team else None,
            "url": f"/e/{event.public_id}/projects/{project.public_id}/",
            "tags": [tag.tag for tag in project.search_tags.all()],
            "artifact_kinds": sorted({artifact.kind for artifact in project.search_artifacts}),
        }
        for project in rows
    ]
    return {
        "count": count,
        "next_offset": offset + 50 if offset + 50 < count else None,
        "items": items,
    }


class PublicSearchView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter("q", str),
            OpenApiParameter("tags", str, many=True),
            OpenApiParameter("artifact_kind", str, enum=ArtifactKind.values),
            OpenApiParameter("track", str),
            OpenApiParameter("stage", str),
            OpenApiParameter("offset", int),
        ],
        responses=SearchOutput,
    )
    def get(self, request, event_public_id):
        event = get_public_event(event_public_id)
        data = request.query_params.dict()
        if "tags" in data:
            data["tags"] = request.query_params.getlist("tags")
        serializer = SearchQueryInput(data=data)
        serializer.is_valid(raise_exception=True)
        filters = dict(serializer.validated_data)
        offset = filters.pop("offset")
        return Response(search(event, filters, offset))


class TagInput(StrictSearchInput):
    tags = serializers.ListField(child=serializers.SlugField(max_length=30), max_length=10)

    def validate(self, attrs):
        attrs["tags"] = sorted({tag.lower() for tag in attrs["tags"]})
        return attrs


class ProjectTagsView(ProjectView):
    @extend_schema(responses=TagInput)
    def get(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.get_project()
        if not project.memberships.filter(user=request.user).exists():
            raise PermissionDenied("Only a project member can read tag management.")
        return Response({"tags": list(project.search_tags.values_list("tag", flat=True))})

    @extend_schema(request=TagInput, responses=TagInput)
    def put(self, request, workspace_public_id, event_public_id, project_public_id):
        serializer = TagInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=self.get_event().pk)
            if event.status == EventStatus.ARCHIVED:
                raise ValidationError("Archived event tags cannot be changed.")
            project = get_object_or_404(
                Project.objects.select_for_update(), event=event, public_id=project_public_id
            )
            if not project.memberships.filter(user=request.user).exists():
                raise PermissionDenied("Only a project member can edit tags.")
            before = list(project.search_tags.values_list("tag", flat=True))
            tags = serializer.validated_data["tags"]
            project.search_tags.all().delete()
            ProjectSearchTag.objects.bulk_create(
                [ProjectSearchTag(project=project, tag=tag) for tag in tags]
            )
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="project.tags_updated",
                target=project,
                metadata={"event_id": str(event.public_id), "before": before, "after": tags},
            )
        return Response({"tags": tags})


class SavedSearchInput(StrictSearchInput):
    name = serializers.CharField(max_length=80)
    filters = SearchFilters()


class SavedSearchOutput(serializers.ModelSerializer):
    class Meta:
        model = SavedPublicSearch
        fields = ["public_id", "name", "filters", "created_at"]
        read_only_fields = fields


class SavedSearchListView(ProjectView):
    @extend_schema(responses=SavedSearchOutput(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        return Response(
            SavedSearchOutput(event.saved_searches.filter(owner=request.user)[:50], many=True).data
        )

    @extend_schema(request=SavedSearchInput, responses={201: SavedSearchOutput})
    def post(self, request, workspace_public_id, event_public_id):
        serializer = SavedSearchInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                event = Event.objects.select_for_update().get(pk=self.get_event().pk)
                get_public_event(event.public_id)
                if event.saved_searches.filter(owner=request.user).count() >= 50:
                    raise ValidationError("At most 50 saved views per event.")
                saved = SavedPublicSearch.objects.create(
                    event=event,
                    owner=request.user,
                    name=serializer.validated_data["name"],
                    filters=serializer.data["filters"],
                )
        except IntegrityError as exc:
            raise ValidationError({"name": "A saved view with this name already exists."}) from exc
        return Response(SavedSearchOutput(saved).data, status=201)


class SavedSearchDetailView(ProjectView):
    def get_saved(self):
        return get_object_or_404(
            SavedPublicSearch,
            event=self.get_event(),
            owner=self.request.user,
            public_id=self.kwargs["view_public_id"],
        )

    @extend_schema(parameters=[OpenApiParameter("offset", int)], responses=SearchOutput)
    def get(self, request, workspace_public_id, event_public_id, view_public_id):
        saved = self.get_saved()
        query = SearchQueryInput(data={**saved.filters, **request.query_params.dict()})
        if set(request.query_params) - {"offset"}:
            raise ValidationError("Only offset may override a saved view.")
        query.is_valid(raise_exception=True)
        filters = dict(query.validated_data)
        offset = filters.pop("offset")
        return Response(search(get_public_event(saved.event.public_id), filters, offset))

    @extend_schema(request=None, responses={204: None})
    def delete(self, request, workspace_public_id, event_public_id, view_public_id):
        self.get_saved().delete()
        return Response(status=204)
