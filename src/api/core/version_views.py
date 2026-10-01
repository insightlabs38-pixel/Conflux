"""The version comparison endpoints (PD-F002-B02-T05): read-only, any two versions of a source."""

from dataclasses import asdict

from accounts.authentication import CookieSessionAuthentication
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import version_diff
from .mixins import WorkspaceLookupMixin
from .permissions import IsWorkspaceMember

PARAMS = (
    ("event", "form and rubric: the event."),
    ("form", "form: the form."),
    ("plan", "rubric: the evaluation plan."),
)


class VersionInfoSchema(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    at = serializers.CharField(allow_null=True)
    by = serializers.CharField(allow_null=True)
    current = serializers.BooleanField()


class VersionListSchema(serializers.Serializer):
    source = serializers.CharField()
    label = serializers.CharField()
    versions = VersionInfoSchema(many=True)


class VersionDiffSchema(serializers.Serializer):
    source = serializers.CharField()
    older = VersionInfoSchema()
    newer = VersionInfoSchema()
    diff = serializers.JSONField(
        help_text="Either {kind: json, changes: [{path, op, before, after, clipped}], total, "
        "truncated} or {kind: text, hunks: [{lines}], added, removed, truncated}."
    )


class _Base(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    def source(self, key):
        found = version_diff.SOURCES.get(key)
        if found is None:
            raise NotFound()
        return found

    def ref(self, source):
        missing = [n for n in source.params if not self.request.query_params.get(n)]
        if missing:
            raise ValidationError({name: ["This parameter is required."] for name in missing})
        return {name: self.request.query_params[name] for name in source.params}


_QUERY = [OpenApiParameter(n, str, description=d, required=False) for n, d in PARAMS]


class VersionListView(_Base):
    @extend_schema(parameters=_QUERY, responses=VersionListSchema)
    def get(self, request, workspace_public_id, source):
        found = self.source(source)
        listed = version_diff.versions_of(
            source, request.user, self.get_workspace(), self.ref(found)
        )
        if listed is None:
            raise NotFound()
        return Response(
            {"source": source, "label": found.label, "versions": [asdict(v) for v in listed]}
        )


class VersionDiffView(_Base):
    @extend_schema(
        parameters=[
            *_QUERY,
            OpenApiParameter("older", str, description="The version id to compare from."),
            OpenApiParameter("newer", str, description="The version id to compare to."),
        ],
        responses=VersionDiffSchema,
    )
    def get(self, request, workspace_public_id, source):
        found = self.source(source)
        ref = self.ref(found)
        ids = {name: request.query_params.get(name) for name in ("older", "newer")}
        missing = [name for name, value in ids.items() if not value]
        if missing:
            raise ValidationError({name: ["This parameter is required."] for name in missing})
        answer = version_diff.compare(
            source, request.user, self.get_workspace(), ref, ids["older"], ids["newer"]
        )
        if answer is None:
            raise NotFound()
        response = Response(
            {
                "source": answer["source"],
                "older": asdict(answer["older"]),
                "newer": asdict(answer["newer"]),
                "diff": answer["diff"],
            }
        )
        response["Cache-Control"] = "private, no-store"
        return response
