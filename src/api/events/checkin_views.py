"""VS18: volunteer capability -- record and view participant check-ins.
Purely an attendance log; it never touches Membership, teams, or judging.
"""

from accounts.models import User
from core.permissions import require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from workspaces.models import Role

from .models import ParticipantCheckIn
from .serializers import CheckInInputSchema, CheckInSerializer
from .views import OrganizerView


class CheckInListView(OrganizerView):
    permission_classes = [require_roles(Role.VOLUNTEER, Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(responses=CheckInSerializer(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        check_ins = ParticipantCheckIn.objects.filter(event=self.get_event()).select_related(
            "participant", "checked_in_by"
        )
        return Response(CheckInSerializer(check_ins, many=True).data)

    @extend_schema(request=CheckInInputSchema, responses={201: CheckInSerializer})
    def post(self, request, workspace_public_id, event_public_id):
        serializer = CheckInInputSchema(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = self.get_event()
        participant = get_object_or_404(
            User,
            memberships__workspace=self.get_workspace(),
            memberships__role=Role.PARTICIPANT,
            public_id=serializer.validated_data["participant"],
        )
        check_in = ParticipantCheckIn(
            event=event, participant=participant, checked_in_by=request.user
        )
        try:
            check_in.full_clean()
            check_in.save()
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(CheckInSerializer(check_in).data, status=201)
