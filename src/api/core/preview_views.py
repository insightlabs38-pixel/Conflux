"""The preview endpoint (PD-F002-B02-T03): one read-only descriptor for any registered source."""

from accounts.authentication import CookieSessionAuthentication
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import previews
from .mixins import WorkspaceLookupMixin
from .permissions import IsWorkspaceMember


class PreviewReasonSchema(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()


class PreviewFindingSchema(serializers.Serializer):
    level = serializers.ChoiceField(choices=previews.LEVELS)
    code = serializers.CharField()
    message = serializers.CharField()


class PreviewEntrySchema(serializers.Serializer):
    name = serializers.CharField()
    size = serializers.IntegerField(allow_null=True)


class PreviewMediaSchema(serializers.Serializer):
    url = serializers.CharField()
    filename = serializers.CharField()


class PreviewSchema(serializers.Serializer):
    source = serializers.CharField()
    ref = serializers.DictField(child=serializers.CharField())
    name = serializers.CharField()
    content_type = serializers.CharField()
    size = serializers.IntegerField(allow_null=True)
    kind = serializers.ChoiceField(choices=previews.KINDS)
    detected_type = serializers.CharField(allow_blank=True)
    state = serializers.ChoiceField(choices=previews.STATES)
    reason = PreviewReasonSchema(allow_null=True)
    facts = serializers.DictField()
    findings = PreviewFindingSchema(many=True)
    findings_total = serializers.IntegerField()
    text = serializers.CharField(allow_blank=True)
    entries = PreviewEntrySchema(many=True)
    entries_total = serializers.IntegerField()
    media = PreviewMediaSchema(allow_null=True)
    link = serializers.CharField(allow_null=True)
    inspected_at = serializers.CharField(allow_null=True)


class PreviewView(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    @extend_schema(
        parameters=[
            OpenApiParameter(name, str, description=text, required=False)
            for name, text in (
                ("event", "project_artifact: the event."),
                ("project", "project_artifact: the project."),
                ("artifact", "project_artifact: the artifact."),
                ("job", "job_output: the job."),
                ("name", "job_output: the output's file name."),
            )
        ],
        responses=PreviewSchema,
    )
    def get(self, request, workspace_public_id, source):
        registered = previews.SOURCES.get(source)
        if registered is None:
            raise NotFound()
        missing = [name for name in registered.params if not request.query_params.get(name)]
        if missing:
            raise ValidationError({name: ["This parameter is required."] for name in missing})
        ref = {name: request.query_params[name] for name in registered.params}
        found = previews.describe(source, request.user, self.get_workspace(), ref)
        if found is None:
            raise NotFound()
        response = Response(found)
        response["Cache-Control"] = "private, no-store"
        return response
