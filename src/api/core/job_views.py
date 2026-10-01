"""Job endpoints: list, read, cancel, download an output (PD-F002-B01-T05).

Creation is the feature's own endpoint (it returns 202 and the job). Who sees what: the requester
sees their own jobs; organizers and admins see every job of the workspace. Anyone else gets 404,
never 403, so a job's existence does not leak.
"""

import uuid

from accounts.authentication import CookieSessionAuthentication
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role

from . import jobs
from .authz import has_any_role
from .mixins import WorkspaceLookupMixin
from .models import Job, JobArtifact
from .pagination import page_params, paged_response
from .permissions import IsWorkspaceMember


class JobProgressSchema(serializers.Serializer):
    done = serializers.IntegerField(allow_null=True)
    total = serializers.IntegerField(allow_null=True)
    message = serializers.CharField()


class JobErrorSchema(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()


class JobArtifactSchema(serializers.Serializer):
    name = serializers.CharField()
    content_type = serializers.CharField()
    size = serializers.IntegerField()


class JobLogSchema(serializers.Serializer):
    level = serializers.CharField()
    message = serializers.CharField()
    at = serializers.DateTimeField()


class JobSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    kind = serializers.CharField()
    label = serializers.CharField()
    status = serializers.ChoiceField(choices=Job.Status.choices)
    event = serializers.UUIDField(allow_null=True)
    requested_by = serializers.CharField()
    progress = JobProgressSchema(allow_null=True)
    result = serializers.JSONField(allow_null=True)
    error = JobErrorSchema(allow_null=True)
    cancellable = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    started_at = serializers.DateTimeField(allow_null=True)
    finished_at = serializers.DateTimeField(allow_null=True)
    artifacts = JobArtifactSchema(many=True)


class JobDetailSchema(JobSchema):
    params = serializers.JSONField()
    logs = JobLogSchema(many=True)


class _JobView(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    def is_staff(self):
        return has_any_role(self.request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN)

    def visible(self):
        return jobs.visible_to(self.request.user, self.get_workspace())

    def get_job(self):
        return get_object_or_404(self.visible(), public_id=self.kwargs["job_public_id"])


class JobListView(_JobView):
    @extend_schema(
        parameters=[
            OpenApiParameter("event", str, description="Only jobs of this event."),
            OpenApiParameter("kind", str),
            OpenApiParameter("status", str, enum=Job.Status.values),
            OpenApiParameter("limit", int),
            OpenApiParameter("offset", int),
        ],
        responses=JobSchema(many=True),
    )
    def get(self, request, workspace_public_id):
        limit, offset = page_params(request, default=25, maximum=100)
        found = self.visible()
        for name in ("kind", "status"):
            value = request.query_params.get(name)
            if value:
                found = found.filter(**{name: value})
        event = request.query_params.get("event")
        if event:
            try:
                found = found.filter(event__public_id=uuid.UUID(event))
            except ValueError as exc:
                raise ValidationError({"event": "Not a valid event id."}) from exc
        return paged_response(
            request,
            found.prefetch_related("artifacts"),
            lambda page: [jobs.describe(job) for job in page],
            limit=limit,
            offset=offset,
        )


class JobDetailView(_JobView):
    @extend_schema(responses=JobDetailSchema)
    def get(self, request, workspace_public_id, job_public_id):
        return Response(jobs.describe(self.get_job(), detail=True))


class JobCancelView(_JobView):
    @extend_schema(request=None, responses=JobSchema)
    def post(self, request, workspace_public_id, job_public_id):
        job = self.get_job()
        try:
            job = jobs.cancel(job, request.user)
        except jobs.JobStateError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        job = self.get_job()
        return Response(jobs.describe(job))


class JobArtifactView(_JobView):
    @extend_schema(responses={(200, "application/octet-stream"): bytes})
    def get(self, request, workspace_public_id, job_public_id, artifact_name):
        job = self.get_job()
        artifact = get_object_or_404(JobArtifact, job=job, name=artifact_name)
        response = HttpResponse(bytes(artifact.body), content_type=artifact.content_type)
        response["Content-Disposition"] = f'attachment; filename="{artifact.name}"'
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        return response
