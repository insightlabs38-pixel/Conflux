from accounts.authentication import CookieSessionAuthentication
from core.permissions import IsWorkspaceMember
from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from events.models import Event
from projects.models import Project
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Membership, Workspace

from .models import Artifact, ArtifactStatus, ArtifactUploadIntent, can_view_artifact
from .preflight import run_preflight
from .schema import (
    ArtifactSchema,
    ExternalArtifactInputSchema,
    PreflightSchema,
    UploadCompleteInputSchema,
    UploadIntentInputSchema,
    UploadIntentSchema,
)
from .services import begin_upload, complete_upload, create_external_artifact
from .storage import S3Storage
from .validators import validate_artifact


def artifact_payload(artifact):
    latest = artifact.validations.first()
    return {
        "public_id": str(artifact.public_id),
        "kind": artifact.kind,
        "visibility": artifact.visibility,
        "title": artifact.title,
        "external_url": artifact.external_url,
        "content_type": artifact.content_type,
        "byte_size": artifact.byte_size,
        "status": artifact.status,
        "validation": {"outcome": latest.outcome, "detail": latest.detail} if latest else None,
    }


def validation_error(exc):
    return ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


class ProjectArtifactView(APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    def get_workspace(self):
        return get_object_or_404(Workspace, public_id=self.kwargs["workspace_public_id"])

    def get_project(self):
        event = get_object_or_404(
            Event, workspace=self.get_workspace(), public_id=self.kwargs["event_public_id"]
        )
        return get_object_or_404(
            Project,
            event=event,
            public_id=self.kwargs["project_public_id"],
            memberships__user=self.request.user,
        )

    def get_artifact(self):
        return get_object_or_404(
            Artifact, project=self.get_project(), public_id=self.kwargs["artifact_public_id"]
        )

    def can_view(self, artifact):
        roles = Membership.objects.filter(
            workspace=self.get_workspace(), user=self.request.user
        ).values_list("role", flat=True)
        return any(can_view_artifact(artifact, user=self.request.user, role=role) for role in roles)


class ArtifactListView(ProjectArtifactView):
    serializer_class = ArtifactSchema

    def get(self, request, workspace_public_id, event_public_id, project_public_id):
        return Response(
            [
                artifact_payload(artifact)
                for artifact in self.get_project().artifacts.all()
                if self.can_view(artifact)
            ]
        )

    @extend_schema(request=ExternalArtifactInputSchema, responses={201: ArtifactSchema})
    def post(self, request, workspace_public_id, event_public_id, project_public_id):
        try:
            artifact = create_external_artifact(
                self.get_project(),
                request.user,
                kind=request.data.get("kind"),
                visibility=request.data.get("visibility"),
                title=request.data.get("title", ""),
                url=request.data.get("external_url", ""),
            )
        except ModelValidationError as exc:
            raise validation_error(exc) from exc
        return Response(artifact_payload(artifact), status=201)


class UploadIntentView(ProjectArtifactView):
    @extend_schema(request=UploadIntentInputSchema, responses={201: UploadIntentSchema})
    def post(self, request, workspace_public_id, event_public_id, project_public_id):
        if isinstance(request.data.get("byte_size"), bool):
            raise ValidationError({"byte_size": "A valid byte size is required."})
        try:
            byte_size = int(request.data.get("byte_size"))
        except (TypeError, ValueError) as exc:
            raise ValidationError({"byte_size": "A valid byte size is required."}) from exc
        try:
            artifact, intent, upload = begin_upload(
                self.get_project(),
                request.user,
                kind=request.data.get("kind"),
                visibility=request.data.get("visibility"),
                title=request.data.get("title", ""),
                byte_size=byte_size,
                content_type=request.data.get("content_type"),
            )
        except ModelValidationError as exc:
            raise validation_error(exc) from exc
        return Response(
            {
                "artifact": artifact_payload(artifact),
                "intent": str(intent.public_id),
                "expires_at": intent.expires_at,
                "upload": upload,
            },
            status=201,
        )


class UploadCompleteView(ProjectArtifactView):
    @extend_schema(request=UploadCompleteInputSchema, responses=ArtifactSchema)
    def post(
        self,
        request,
        workspace_public_id,
        event_public_id,
        project_public_id,
        artifact_public_id,
        intent_public_id,
    ):
        artifact = self.get_artifact()
        intent = get_object_or_404(
            ArtifactUploadIntent, artifact=artifact, public_id=intent_public_id
        )
        try:
            artifact = complete_upload(intent, request.user, parts=request.data.get("parts"))
        except ModelValidationError as exc:
            raise validation_error(exc) from exc
        return Response(artifact_payload(artifact))


class ArtifactDetailView(ProjectArtifactView):
    serializer_class = ArtifactSchema

    def get(
        self, request, workspace_public_id, event_public_id, project_public_id, artifact_public_id
    ):
        artifact = self.get_artifact()
        if not self.can_view(artifact):
            return Response(status=404)
        payload = artifact_payload(artifact)
        if artifact.status == ArtifactStatus.READY and artifact.object_key:
            payload["download_url"] = S3Storage().presign_get(artifact.object_key)
        return Response(payload)


class ArtifactValidateView(ProjectArtifactView):
    @extend_schema(request=None, responses=ArtifactSchema)
    def post(
        self, request, workspace_public_id, event_public_id, project_public_id, artifact_public_id
    ):
        artifact = self.get_artifact()
        if not self.can_view(artifact) and artifact.created_by_id != request.user.id:
            return Response(status=404)
        evidence = validate_artifact(artifact)
        artifact.refresh_from_db()
        return Response(
            {
                **artifact_payload(artifact),
                "validation": {"outcome": evidence.outcome, "detail": evidence.detail},
            }
        )


class ProjectPreflightView(ProjectArtifactView):
    serializer_class = PreflightSchema

    def get(self, request, workspace_public_id, event_public_id, project_public_id):
        return Response(run_preflight(self.get_project()).as_dict())
