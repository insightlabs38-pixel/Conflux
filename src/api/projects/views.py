from accounts.authentication import CookieSessionAuthentication
from accounts.models import User
from core.permissions import IsWorkspaceMember
from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from events.models import Event
from participation.models import Team
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Workspace

from .models import Project, ProjectMembershipRole
from .serializers import ProjectMembershipSerializer, ProjectSerializer
from .services import add_project_member, create_project


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
    def get(self, request, workspace_public_id, event_public_id):
        projects = Project.objects.filter(
            event=self.get_event(), memberships__user=request.user
        ).distinct()
        return Response(ProjectSerializer(projects, many=True).data)

    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        name = str(request.data.get("name", "")).strip()
        if not name:
            raise ValidationError({"name": "Project name is required."})
        team_id = request.data.get("team")
        team = get_object_or_404(Team, event=event, public_id=team_id) if team_id else None
        try:
            project = create_project(
                event,
                request.user,
                name,
                team=team,
                description=str(request.data.get("description", "")),
            )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(ProjectSerializer(project).data, status=201)


class ProjectDetailView(ProjectView):
    def get(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.get_project()
        if not project.memberships.filter(user=request.user).exists():
            return Response(status=404)
        return Response(ProjectSerializer(project).data)


class ProjectMemberView(ProjectView):
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
