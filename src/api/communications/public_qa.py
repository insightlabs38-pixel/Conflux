from accounts.authentication import CookieSessionAuthentication
from audit.services import record_mutation
from core.authz import has_any_role
from core.permissions import require_roles
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from events.models import PUBLICLY_VISIBLE_STATUSES, Announcement, Event, EventStatus
from events.views import OrganizerView
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role

from .models import EventQuestion


class StrictInput(serializers.Serializer):
    def validate(self, attrs):
        if self.initial_data.keys() - self.fields.keys():
            raise serializers.ValidationError("Unknown fields.")
        return attrs


class QuestionInput(StrictInput):
    question = serializers.CharField(max_length=2000)


class QuestionOutput(serializers.ModelSerializer):
    class Meta:
        model = EventQuestion
        fields = [
            "public_id",
            "question",
            "answer",
            "status",
            "version",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PublicAnnouncementOutput(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ["public_id", "title", "body", "created_at"]
        read_only_fields = fields


class QuestionReviewInput(StrictInput):
    version = serializers.IntegerField(min_value=1)
    status = serializers.ChoiceField(choices=EventQuestion.Status.choices)
    answer = serializers.CharField(max_length=4000, allow_blank=True, required=False)
    note = serializers.CharField(max_length=2000)


class AnnouncementReviewInput(StrictInput):
    version = serializers.IntegerField(min_value=1)
    status = serializers.ChoiceField(choices=["published", "hidden"])
    note = serializers.CharField(max_length=2000)


class AnnouncementReviewOutput(PublicAnnouncementOutput):
    class Meta(PublicAnnouncementOutput.Meta):
        fields = PublicAnnouncementOutput.Meta.fields + ["version", "hidden_at"]
        read_only_fields = fields


class PageQuery(serializers.Serializer):
    offset = serializers.IntegerField(default=0, min_value=0, max_value=1000000)


def page(request, queryset):
    query = PageQuery(data=request.query_params)
    query.is_valid(raise_exception=True)
    offset = query.validated_data["offset"]
    return queryset[offset : offset + 50]


def public_event(event_public_id):
    return get_object_or_404(
        Event, public_id=event_public_id, is_public=True, status__in=PUBLICLY_VISIBLE_STATUSES
    )


class PublicQuestionsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[OpenApiParameter("offset", int)], responses=QuestionOutput(many=True)
    )
    def get(self, request, event_public_id):
        event = public_event(event_public_id)
        rows = page(request, event.questions.filter(status=EventQuestion.Status.PUBLISHED))
        return Response(QuestionOutput(rows, many=True).data)


class PublicAnnouncementsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[OpenApiParameter("offset", int)], responses=PublicAnnouncementOutput(many=True)
    )
    def get(self, request, event_public_id):
        event = public_event(event_public_id)
        rows = page(request, event.announcements.filter(hidden_at=None))
        return Response(PublicAnnouncementOutput(rows, many=True).data)


class QuestionsView(OrganizerView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.PARTICIPANT, Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(
        parameters=[OpenApiParameter("offset", int)], responses=QuestionOutput(many=True)
    )
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        rows = event.questions.all()
        if not has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN):
            rows = rows.filter(author=request.user)
        return Response(QuestionOutput(page(request, rows), many=True).data)

    @extend_schema(request=QuestionInput, responses={201: QuestionOutput})
    def post(self, request, workspace_public_id, event_public_id):
        serializer = QuestionInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=self.get_event().pk)
            if not event.is_public or event.status != EventStatus.OPEN:
                raise ValidationError("Questions can only be submitted to open public events.")
            question = EventQuestion.objects.create(
                event=event, author=request.user, **serializer.validated_data
            )
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="question.submitted",
                target=question,
                metadata={"event_id": str(event.public_id)},
            )
        return Response(QuestionOutput(question).data, status=201)


class CommunicationReviewView(OrganizerView):
    model = EventQuestion
    input_serializer = QuestionReviewInput
    output_serializer = QuestionOutput

    @extend_schema(request=QuestionReviewInput, responses={200: QuestionOutput, 409: None})
    def post(self, request, workspace_public_id, event_public_id, source_public_id):
        event = self.get_event()
        serializer = self.input_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=event.pk)
            self.ensure_mutable(event)
            source = get_object_or_404(
                self.model.objects.select_for_update(), event=event, public_id=source_public_id
            )
            if source.version != data["version"]:
                return Response(
                    {"detail": "Communication changed; refresh before reviewing."}, status=409
                )
            before = self.output_serializer(source).data
            if self.model is EventQuestion:
                answer = data.get("answer", source.answer)
                if data["status"] == EventQuestion.Status.PUBLISHED and not answer.strip():
                    raise ValidationError({"answer": "A published question requires an answer."})
                source.answer = answer
                source.status = data["status"]
                action = "question.reviewed"
            else:
                source.hidden_at = timezone.now() if data["status"] == "hidden" else None
                action = "announcement.reviewed"
            source.version += 1
            source.save()
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action=action,
                target=source,
                metadata={
                    "event_id": str(event.public_id),
                    "note": data["note"],
                    "before": before,
                    "after": self.output_serializer(source).data,
                },
            )
        return Response(self.output_serializer(source).data)


class AnnouncementReviewView(CommunicationReviewView):
    model = Announcement
    input_serializer = AnnouncementReviewInput
    output_serializer = AnnouncementReviewOutput

    @extend_schema(
        request=AnnouncementReviewInput, responses={200: AnnouncementReviewOutput, 409: None}
    )
    def post(self, request, workspace_public_id, event_public_id, source_public_id):
        return super().post(request, workspace_public_id, event_public_id, source_public_id)
