from accounts.authentication import CookieSessionAuthentication
from accounts.models import User
from core.permissions import IsWorkspaceMember
from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from events.models import Event, Track
from events.views import OrganizerView
from participation.models import Team
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from stages.models import Stage
from workspaces.models import Workspace

from .diff import diff_snapshots
from .models import Project, ProjectMembershipRole, Submission
from .schema import (
    ProjectCreateInputSchema,
    ProjectPatchInputSchema,
    SubmissionDiffSchema,
    SubmissionDraftInputSchema,
    SubmissionFinalizeInputSchema,
    SubmissionReceiptSchema,
    SubmissionReopenInputSchema,
    SubmissionSchema,
    SubmissionStageSchema,
)
from .serializers import ProjectMembershipSerializer, ProjectSerializer
from .services import add_project_member, create_project, update_project
from .submissions import finalize_submission, reopen_submission, save_draft


class ProjectView(APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    def get_workspace(self):
        return get_object_or_404(Workspace, public_id=self.kwargs["workspace_public_id"])

    def get_event(self):
        return get_object_or_404(
            Event, workspace=self.get_workspace(), public_id=self.kwargs["event_public_id"]
        )

    def get_project(self):
        return get_object_or_404(
            Project, event=self.get_event(), public_id=self.kwargs["project_public_id"]
        )


class ProjectListView(ProjectView):
    serializer_class = ProjectSerializer

    def get(self, request, workspace_public_id, event_public_id):
        projects = Project.objects.filter(
            event=self.get_event(), memberships__user=request.user
        ).distinct()
        return Response(ProjectSerializer(projects, many=True).data)

    @extend_schema(request=ProjectCreateInputSchema, responses={201: ProjectSerializer})
    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        name = str(request.data.get("name", "")).strip()
        if not name:
            raise ValidationError({"name": "Project name is required."})
        team_id = request.data.get("team")
        team = get_object_or_404(Team, event=event, public_id=team_id) if team_id else None
        track_id = request.data.get("track")
        track = get_object_or_404(Track, event=event, public_id=track_id) if track_id else None
        try:
            project = create_project(
                event,
                request.user,
                name,
                team=team,
                track=track,
                description=str(request.data.get("description", "")),
            )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(ProjectSerializer(project).data, status=201)


class ProjectDetailView(ProjectView):
    serializer_class = ProjectSerializer

    def get(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.get_project()
        if not project.memberships.filter(user=request.user).exists():
            return Response(status=404)
        return Response(ProjectSerializer(project).data)

    @extend_schema(request=ProjectPatchInputSchema, responses=ProjectSerializer)
    def patch(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.get_project()
        if not project.memberships.filter(user=request.user).exists():
            return Response(status=404)
        event = self.get_event()
        track_set = "track" in request.data
        track_id = request.data.get("track")
        track = get_object_or_404(Track, event=event, public_id=track_id) if track_id else None
        try:
            project = update_project(
                project,
                request.user,
                name=request.data.get("name"),
                description=request.data.get("description"),
                track=track,
                track_set=track_set,
            )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(ProjectSerializer(project).data)


class ProjectMemberView(ProjectView):
    serializer_class = ProjectMembershipSerializer

    @extend_schema(
        request=inline_serializer(
            "AddProjectMemberInput", fields={"user": serializers.UUIDField()}
        ),
        responses={201: ProjectMembershipSerializer},
    )
    def post(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.get_project()
        if not project.memberships.filter(
            user=request.user, role=ProjectMembershipRole.OWNER
        ).exists():
            return Response(status=404)
        target = get_object_or_404(User, public_id=request.data.get("user"))
        try:
            membership = add_project_member(project, request.user, target)
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(ProjectMembershipSerializer(membership).data, status=201)


def submission_payload(submission):
    current = submission.current_version
    return {
        "public_id": str(submission.public_id),
        "stage": str(submission.stage.public_id),
        "status": submission.status,
        "draft_payload": submission.draft_payload,
        "draft_revision": submission.draft_revision,
        "current_version": str(current.public_id) if current else None,
        "versions": [
            {
                "public_id": str(version.public_id),
                "number": version.number,
                "digest": version.digest,
                "finalized_at": version.finalized_at,
                "finalized_by": str(version.finalized_by.public_id),
            }
            for version in submission.versions.select_related("finalized_by").all()
        ],
    }


class ProjectSubmissionView(ProjectView):
    def get_project(self):
        return get_object_or_404(
            Project,
            event=self.get_event(),
            public_id=self.kwargs["project_public_id"],
            memberships__user=self.request.user,
        )

    def get_stage(self):
        return get_object_or_404(
            Stage, event=self.get_event(), public_id=self.kwargs["stage_public_id"]
        )


class SubmissionStageListView(ProjectSubmissionView):
    @extend_schema(responses=SubmissionStageSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.get_project()
        submissions = {
            item.stage_id: item
            for item in Submission.objects.filter(project=project).select_related(
                "stage", "current_version"
            )
        }
        return Response(
            [
                {
                    "public_id": str(stage.public_id),
                    "name": stage.name,
                    "submission": submission_payload(submissions[stage.pk])
                    if stage.pk in submissions
                    else None,
                }
                for stage in Stage.objects.filter(event=project.event)
            ]
        )


class SubmissionDetailView(ProjectSubmissionView):
    @extend_schema(responses=SubmissionSchema)
    def get(
        self, request, workspace_public_id, event_public_id, project_public_id, stage_public_id
    ):
        submission = get_object_or_404(
            Submission, project=self.get_project(), stage=self.get_stage()
        )
        return Response(submission_payload(submission))

    @extend_schema(request=SubmissionDraftInputSchema, responses=SubmissionSchema)
    def put(
        self, request, workspace_public_id, event_public_id, project_public_id, stage_public_id
    ):
        try:
            submission = save_draft(
                self.get_project(),
                self.get_stage(),
                request.user,
                payload=request.data.get("draft_payload"),
                revision=request.data.get("draft_revision"),
            )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(submission_payload(submission))


class SubmissionFinalizeView(ProjectSubmissionView):
    @extend_schema(
        request=SubmissionFinalizeInputSchema,
        responses={200: SubmissionReceiptSchema, 201: SubmissionReceiptSchema},
    )
    def post(
        self, request, workspace_public_id, event_public_id, project_public_id, stage_public_id
    ):
        try:
            submission, version, created = finalize_submission(
                self.get_project(),
                self.get_stage(),
                request.user,
                revision=request.data.get("draft_revision"),
            )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(
            {"submission": submission_payload(submission), "receipt": str(version.public_id)},
            status=201 if created else 200,
        )


class OrganizerSubmissionView(OrganizerView):
    """Allow organizers to inspect submissions without project membership."""

    def get_project(self):
        return get_object_or_404(
            Project, event=self.get_event(), public_id=self.kwargs["project_public_id"]
        )

    def get_stage(self):
        return get_object_or_404(
            Stage, event=self.get_event(), public_id=self.kwargs["stage_public_id"]
        )


class SubmissionReopenView(OrganizerSubmissionView):
    @extend_schema(request=SubmissionReopenInputSchema, responses=SubmissionSchema)
    def post(
        self, request, workspace_public_id, event_public_id, project_public_id, stage_public_id
    ):
        serializer = SubmissionReopenInputSchema(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            submission = reopen_submission(
                self.get_project(),
                self.get_stage(),
                request.user,
                reason=serializer.validated_data.get("reason", ""),
            )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(submission_payload(submission))


def _find_version(versions, raw_number, field_name):
    if raw_number is None:
        return None
    try:
        number = int(raw_number)
    except (TypeError, ValueError):
        raise ValidationError({field_name: "Must be a version number."}) from None
    for version in versions:
        if version.number == number:
            return version
    raise ValidationError({field_name: f"No version numbered {number} exists."})


class SubmissionDiffView(OrganizerSubmissionView):
    """Compare two immutable versions, defaulting to the most recent pair."""

    @extend_schema(responses=SubmissionDiffSchema)
    def get(
        self, request, workspace_public_id, event_public_id, project_public_id, stage_public_id
    ):
        submission = get_object_or_404(
            Submission, project=self.get_project(), stage=self.get_stage()
        )
        versions = list(submission.versions.order_by("number"))
        if len(versions) < 2:
            raise ValidationError(
                {"detail": "This submission has fewer than two versions to diff."}
            )
        to_version = _find_version(versions, request.GET.get("to"), "to") or versions[-1]
        from_version = _find_version(versions, request.GET.get("from"), "from")
        if from_version is None:
            previous = [version for version in versions if version.number < to_version.number]
            if not previous:
                raise ValidationError({"from": "No earlier version exists."})
            from_version = previous[-1]
        if from_version.number >= to_version.number:
            raise ValidationError({"from": "Must be earlier than the to version."})
        return Response(
            {
                "from_version": from_version.number,
                "to_version": to_version.number,
                "diff": diff_snapshots(from_version.snapshot, to_version.snapshot),
            }
        )
