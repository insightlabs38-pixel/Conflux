import uuid

from django.core.exceptions import ValidationError as ModelValidationError
from drf_spectacular.utils import OpenApiParameter, extend_schema
from events.views import OrganizerView
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import ModerationReview
from .moderation import KINDS, ChangedEvidence, queue, review_data, review_source


class ModerationQuery(serializers.Serializer):
    kind = serializers.ChoiceField(choices=KINDS, required=False)
    offset = serializers.IntegerField(default=0, min_value=0, max_value=1000000)


class ModerationReviewInput(serializers.Serializer):
    kind = serializers.ChoiceField(choices=KINDS)
    source_key = serializers.CharField(max_length=64)
    evidence_digest = serializers.RegexField(r"^[a-f0-9]{64}$")
    disposition = serializers.ChoiceField(
        choices=[
            "dismiss",
            "escalate",
            "resolve",
            "hide",
            "acknowledge",
            "approve",
            "reject",
            "waitlist",
        ]
    )
    note = serializers.CharField(max_length=2000)

    def validate(self, attrs):
        key = attrs["source_key"]
        if attrs["kind"] == "duplicate":
            if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
                raise serializers.ValidationError({"source_key": "Expected an artifact SHA256."})
        else:
            try:
                attrs["source_key"] = str(uuid.UUID(key))
            except ValueError as exc:
                raise serializers.ValidationError(
                    {"source_key": "Expected a source UUID."}
                ) from exc
        if self.initial_data.keys() - self.fields.keys():
            raise serializers.ValidationError("Unknown review fields.")
        return attrs


class ModerationReviewResponse(serializers.Serializer):
    public_id = serializers.UUIDField()
    kind = serializers.CharField()
    source_key = serializers.CharField()
    evidence_digest = serializers.CharField()
    evidence = serializers.JSONField()
    disposition = serializers.CharField()
    note = serializers.CharField()
    actor = serializers.UUIDField()
    created_at = serializers.DateTimeField()


class ModerationQueueResponse(serializers.Serializer):
    sections = serializers.ListField(child=serializers.JSONField())


_PARAMETERS = [OpenApiParameter("kind", str, enum=list(KINDS)), OpenApiParameter("offset", int)]


class ModerationQueueView(OrganizerView):
    @extend_schema(parameters=_PARAMETERS, responses=ModerationQueueResponse)
    def get(self, request, workspace_public_id, event_public_id):
        query = ModerationQuery(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response(queue(self.get_event(), **query.validated_data))


class ModerationReviewsView(OrganizerView):
    @extend_schema(parameters=_PARAMETERS, responses=ModerationReviewResponse(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        query = ModerationQuery(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        reviews = ModerationReview.objects.filter(event=self.get_event()).select_related("actor")
        if params.get("kind"):
            reviews = reviews.filter(kind=params["kind"])
        offset = params["offset"]
        reviews = reviews.order_by("-created_at", "-pk")[offset : offset + 50]
        return Response([review_data(review) for review in reviews])

    @extend_schema(request=ModerationReviewInput, responses={201: ModerationReviewResponse})
    def post(self, request, workspace_public_id, event_public_id):
        serializer = ModerationReviewInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            review = review_source(
                event=self.get_event(), actor=request.user, **serializer.validated_data
            )
        except ChangedEvidence as exc:
            return Response({"detail": str(exc)}, status=409)
        except ModelValidationError as exc:
            raise ValidationError(exc.messages) from exc
        return Response(review_data(review), status=201)
