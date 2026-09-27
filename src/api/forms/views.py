from accounts.authentication import CookieSessionAuthentication
from core.permissions import IsWorkspaceMember
from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from events.models import Event
from projects.models import Project
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Workspace

from .models import FormResponse, FormVersion
from .services import save_response
from .validation import field_visible


def participant_answers(response):
    if response is None:
        return {}
    values = {answer.field_id: answer.value for answer in response.answers.all()}
    fields = {field["id"]: field for field in response.version.schema["fields"]}
    return {
        field_id: value
        for field_id, value in values.items()
        if field_id in fields and field_visible(fields[field_id], "participant", values)
    }


class ProjectFormResponseView(APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    def get_workspace(self):
        return get_object_or_404(Workspace, public_id=self.kwargs["workspace_public_id"])

    def get_objects(self, request):
        event = get_object_or_404(
            Event, workspace=self.get_workspace(), public_id=self.kwargs["event_public_id"]
        )
        project = get_object_or_404(
            Project,
            event=event,
            public_id=self.kwargs["project_public_id"],
            memberships__user=request.user,
        )
        version = get_object_or_404(
            FormVersion, definition__event=event, public_id=self.kwargs["version_public_id"]
        )
        return project, version

    def get(
        self, request, workspace_public_id, event_public_id, project_public_id, version_public_id
    ):
        project, version = self.get_objects(request)
        response = FormResponse.objects.filter(project=project, version=version).first()
        return Response(
            {
                "version": str(version.public_id),
                "answers": participant_answers(response),
            }
        )

    def put(
        self, request, workspace_public_id, event_public_id, project_public_id, version_public_id
    ):
        project, version = self.get_objects(request)
        try:
            response = save_response(project, version, request.user, request.data.get("answers"))
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(
            {
                "version": str(version.public_id),
                "answers": participant_answers(response),
            }
        )
