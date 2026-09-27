"""VS18: mentor and sponsor capabilities. Mentor notes are private to
organizers/admins/mentors (never the project's own participants, never
scoring). The sponsor view is read-only, no different in sensitivity from
what a judge already sees minus scores.
"""

from core.permissions import require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from workspaces.models import Role

from .models import MentorNote, Project
from .serializers import MentorNoteInputSchema, MentorNoteSerializer, SponsorProjectSchema
from .views import ProjectView


class MentorNoteListView(ProjectView):
    permission_classes = [require_roles(Role.MENTOR, Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(responses=MentorNoteSerializer(many=True))
    def get(self, request, workspace_public_id, event_public_id, project_public_id):
        notes = MentorNote.objects.filter(project=self.get_project()).select_related("mentor")
        return Response(MentorNoteSerializer(notes, many=True).data)

    @extend_schema(request=MentorNoteInputSchema, responses={201: MentorNoteSerializer})
    def post(self, request, workspace_public_id, event_public_id, project_public_id):
        serializer = MentorNoteInputSchema(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = MentorNote(
            project=self.get_project(),
            mentor=request.user,
            body=serializer.validated_data["body"],
        )
        try:
            note.full_clean()
            note.save()
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(MentorNoteSerializer(note).data, status=201)


class SponsorProjectListView(ProjectView):
    permission_classes = [require_roles(Role.SPONSOR, Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(responses=SponsorProjectSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        projects = Project.objects.filter(event=self.get_event()).select_related("team", "track")
        return Response(
            [
                {
                    "public_id": str(project.public_id),
                    "name": project.name,
                    "team_name": project.team.name if project.team_id else None,
                    "track_name": project.track.name if project.track_id else None,
                }
                for project in projects
            ]
        )
