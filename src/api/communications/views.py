from accounts.authentication import CookieSessionAuthentication
from audit.services import record_mutation
from core.permissions import IsWorkspaceMember
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from events.views import OrganizerView
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Workspace

from .audiences import AUDIENCE_KINDS, resolve_audience
from .checklist import compute_launch_checklist
from .models import MessageRecipient, Reminder
from .operations import compute_operations_summary
from .operator_console import compute_operator_console
from .schema import (
    AudienceKindSchema,
    AudiencePreviewInputSchema,
    AudiencePreviewSchema,
    InboxMessageSchema,
    LaunchChecklistSchema,
    MessageInputSchema,
    MessageSchema,
    OperationsSummarySchema,
    OperatorConsoleSchema,
    ReminderInputSchema,
    ReminderSchema,
)
from .services import mark_read, send_message

_PAGE_SIZE = 100


def _offset(request):
    try:
        return max(int(request.query_params.get("offset", 0)), 0)
    except ValueError:
        return 0


def _message_data(message):
    return {
        "public_id": str(message.public_id),
        "subject": message.subject,
        "body": message.body,
        "audience_kind": message.audience_kind,
        "audience_params": message.audience_params,
        "recipient_count": message.recipient_count,
        "email_failure_count": message.email_failure_count,
        "created_at": message.created_at,
    }


def _reminder_data(reminder):
    return {
        "public_id": str(reminder.public_id),
        "kind": reminder.kind,
        "due_at": reminder.due_at,
        "audience_kind": reminder.audience_kind,
        "audience_params": reminder.audience_params,
        "subject": reminder.subject,
        "body": reminder.body,
        "status": "sent"
        if reminder.sent_message_id
        else "cancelled"
        if reminder.cancelled_at
        else "pending",
        "sent_message": str(reminder.sent_message.public_id) if reminder.sent_message_id else None,
        "cancelled_at": reminder.cancelled_at,
        "last_error": reminder.last_error,
    }


class OperationsSummaryView(OrganizerView):
    @extend_schema(responses=OperationsSummarySchema)
    def get(self, request, workspace_public_id, event_public_id):
        return Response(compute_operations_summary(self.get_event()))


class OperatorConsoleView(OrganizerView):
    @extend_schema(responses=OperatorConsoleSchema)
    def get(self, request, workspace_public_id):
        return Response(compute_operator_console(self.get_workspace()))


class LaunchChecklistView(OrganizerView):
    @extend_schema(responses=LaunchChecklistSchema)
    def get(self, request, workspace_public_id, event_public_id):
        return Response(compute_launch_checklist(self.get_event()))


class AudienceListView(OrganizerView):
    @extend_schema(responses=AudienceKindSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        return Response(
            [
                {
                    "key": kind.key,
                    "label": kind.label,
                    "param_names": list(kind.param_names),
                    "options": kind.options(event),
                }
                for kind in AUDIENCE_KINDS.values()
            ]
        )


class AudiencePreviewView(OrganizerView):
    @extend_schema(request=AudiencePreviewInputSchema, responses=AudiencePreviewSchema)
    def post(self, request, workspace_public_id, event_public_id):
        data = AudiencePreviewInputSchema(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            users = list(
                resolve_audience(
                    self.get_event(),
                    data.validated_data["audience_kind"],
                    data.validated_data.get("audience_params", {}),
                )
            )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(
            {
                "count": len(users),
                "sample": [
                    {"public_id": str(user.public_id), "username": user.username}
                    for user in users[:10]
                ],
            }
        )


class MessageListCreateView(OrganizerView):
    @extend_schema(responses=MessageSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        offset = _offset(request)
        messages = self.get_event().messages.all()[offset : offset + _PAGE_SIZE]
        return Response([_message_data(message) for message in messages])

    @extend_schema(request=MessageInputSchema, responses={201: MessageSchema})
    def post(self, request, workspace_public_id, event_public_id):
        data = MessageInputSchema(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            message = send_message(
                event=self.get_event(),
                actor=request.user,
                subject=data.validated_data["subject"],
                body=data.validated_data["body"],
                audience_kind=data.validated_data["audience_kind"],
                audience_params=data.validated_data.get("audience_params", {}),
            )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(_message_data(message), status=201)


class ReminderListCreateView(OrganizerView):
    @extend_schema(responses=ReminderSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        offset = _offset(request)
        reminders = self.get_event().reminders.select_related("sent_message")[
            offset : offset + _PAGE_SIZE
        ]
        return Response([_reminder_data(item) for item in reminders])

    @extend_schema(request=ReminderInputSchema, responses={201: ReminderSchema})
    def post(self, request, workspace_public_id, event_public_id):
        serializer = ReminderInputSchema(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if data["due_at"] <= timezone.now():
            raise ValidationError({"due_at": "Reminder must be scheduled in the future."})
        event = self.get_event()
        try:
            resolve_audience(event, data["audience_kind"], data.get("audience_params", {}))
            with transaction.atomic():
                reminder = Reminder(event=event, created_by=request.user, **data)
                reminder.full_clean()
                reminder.save()
                record_mutation(
                    actor=request.user,
                    workspace=event.workspace,
                    action="reminder.scheduled",
                    target=reminder,
                    metadata={"kind": reminder.kind, "due_at": reminder.due_at.isoformat()},
                )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(_reminder_data(reminder), status=201)


class ReminderCancelView(OrganizerView):
    @extend_schema(request=None, responses=ReminderSchema)
    def post(self, request, workspace_public_id, event_public_id, reminder_public_id):
        with transaction.atomic():
            reminder = get_object_or_404(
                Reminder.objects.select_for_update(of=("self",)).select_related("sent_message"),
                event=self.get_event(),
                public_id=reminder_public_id,
            )
            if reminder.sent_message_id:
                raise ValidationError({"detail": "A sent reminder cannot be cancelled."})
            if reminder.cancelled_at is None:
                reminder.cancelled_at = timezone.now()
                reminder.save(update_fields=["cancelled_at"])
                record_mutation(
                    actor=request.user,
                    workspace=reminder.event.workspace,
                    action="reminder.cancelled",
                    target=reminder,
                )
        return Response(_reminder_data(reminder))


class MemberView(APIView):
    """Any workspace member may read their own inbox -- not organizer-only,
    the same split events.views.OrganizerView/participation.ParticipantView
    already draw.
    """

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    def get_workspace(self):
        if not hasattr(self, "_workspace"):
            self._workspace = get_object_or_404(
                Workspace, public_id=self.kwargs["workspace_public_id"]
            )
        return self._workspace


class InboxListView(MemberView):
    @extend_schema(responses=InboxMessageSchema(many=True))
    def get(self, request, workspace_public_id):
        offset = _offset(request)
        recipients = (
            MessageRecipient.objects.filter(
                user=request.user, message__event__workspace=self.get_workspace()
            )
            .select_related("message", "message__event")
            .order_by("-message__created_at", "-id")[offset : offset + _PAGE_SIZE]
        )
        return Response(
            [
                {
                    "public_id": str(recipient.public_id),
                    "subject": recipient.message.subject,
                    "body": recipient.message.body,
                    "event": str(recipient.message.event.public_id),
                    "event_name": recipient.message.event.name,
                    "created_at": recipient.message.created_at,
                    "read_at": recipient.read_at,
                }
                for recipient in recipients
            ]
        )


class InboxReadView(MemberView):
    @extend_schema(request=None, responses=InboxMessageSchema)
    def post(self, request, workspace_public_id, recipient_public_id):
        recipient = get_object_or_404(
            MessageRecipient.objects.select_related("message", "message__event"),
            public_id=recipient_public_id,
            message__event__workspace=self.get_workspace(),
        )
        try:
            recipient = mark_read(recipient, request.user)
        except ModelValidationError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(
            {
                "public_id": str(recipient.public_id),
                "subject": recipient.message.subject,
                "body": recipient.message.body,
                "event": str(recipient.message.event.public_id),
                "event_name": recipient.message.event.name,
                "created_at": recipient.message.created_at,
                "read_at": recipient.read_at,
            }
        )
