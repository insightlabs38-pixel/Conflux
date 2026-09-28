"""Reviewer access to submitted evidence and safe inspection (PVS08).

Judges see only what an artifact's visibility grants their role, and only for
projects they are expected to evaluate; organizers see everything in their
workspace. Participants inspect their own artifacts before anyone else does.
"""

from accounts.authentication import CookieSessionAuthentication
from core.authz import has_any_role
from core.permissions import IsWorkspaceMember
from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from evaluations.candidates import judge_candidates
from evaluations.models import EvaluationPlan
from events.models import Event
from projects.models import Project
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role, Workspace

from .models import Artifact, ArtifactStatus, ArtifactVisibility
from .services import inspection_data, run_inspection
from .storage import S3Storage

REVIEW_ROLES = (Role.JUDGE, Role.ORGANIZER, Role.ADMIN)


class ReviewBase(APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    def get_workspace(self):
        if not hasattr(self, "_workspace"):
            self._workspace = get_object_or_404(
                Workspace, public_id=self.kwargs["workspace_public_id"]
            )
        return self._workspace

    def get_project(self):
        event = get_object_or_404(
            Event, workspace=self.get_workspace(), public_id=self.kwargs["event_public_id"]
        )
        return get_object_or_404(Project, event=event, public_id=self.kwargs["project_public_id"])

    def reviewer_scope(self, project):
        """'all', 'judge' or None for the requester on this project."""
        user, workspace = self.request.user, self.get_workspace()
        if has_any_role(user, workspace, Role.ORGANIZER, Role.ADMIN):
            return "all"
        if project.memberships.filter(user=user).exists():
            return "member"
        if has_any_role(user, workspace, Role.JUDGE):
            plans = EvaluationPlan.objects.filter(stage__event=project.event)
            if any(judge_candidates(plan, user).filter(pk=project.pk).exists() for plan in plans):
                return "judge"
        return None

    def visible(self, artifact, scope):
        if scope in ("all", "member"):
            return True
        return artifact.visibility in (ArtifactVisibility.PUBLIC, ArtifactVisibility.JUDGE)

    def get_artifact(self, project, scope):
        artifact = get_object_or_404(
            Artifact, project=project, public_id=self.kwargs["artifact_public_id"]
        )
        if scope is None or not self.visible(artifact, scope):
            raise NotFound()
        return artifact


class ReviewArtifactListView(ReviewBase):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.get_project()
        scope = self.reviewer_scope(project)
        if scope is None or scope == "member":
            raise NotFound()
        rows = []
        for artifact in project.artifacts.order_by("created_at", "pk"):
            if not self.visible(artifact, scope):
                continue
            latest = artifact.inspections.first()
            download = None
            if (
                artifact.object_key
                and artifact.status == ArtifactStatus.READY
                and (latest is None or latest.verdict != "blocked")
            ):
                download = S3Storage().presign_get(
                    artifact.object_key, download_filename=artifact.title
                )
            rows.append(
                {
                    "public_id": str(artifact.public_id),
                    "kind": artifact.kind,
                    "visibility": artifact.visibility,
                    "title": artifact.title,
                    "external_url": artifact.external_url,
                    "status": artifact.status,
                    "byte_size": artifact.byte_size,
                    "inspection": inspection_data(latest) if latest else None,
                    "download_url": download,
                }
            )
        return Response(rows)


class InspectionView(ReviewBase):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(
        self, request, workspace_public_id, event_public_id, project_public_id, artifact_public_id
    ):
        project = self.get_project()
        artifact = self.get_artifact(project, self.reviewer_scope(project))
        latest = artifact.inspections.first()
        if latest is None:
            raise NotFound("This artifact has not been inspected yet.")
        return Response(inspection_data(latest))

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(
        self, request, workspace_public_id, event_public_id, project_public_id, artifact_public_id
    ):
        project = self.get_project()
        artifact = self.get_artifact(project, self.reviewer_scope(project))
        try:
            record = run_inspection(artifact, request.user)
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(inspection_data(record))
