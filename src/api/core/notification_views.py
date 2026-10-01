"""A person's own notification choices (PD-F002-B02-T04)."""

from accounts.authentication import CookieSessionAuthentication
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import notifications
from .mixins import WorkspaceLookupMixin
from .permissions import IsWorkspaceMember


class NotificationChannelSchema(serializers.Serializer):
    channel = serializers.CharField()
    label = serializers.CharField()
    enabled = serializers.BooleanField()
    locked = serializers.BooleanField()
    default = serializers.BooleanField()
    chosen = serializers.BooleanField()


class NotificationCategorySchema(serializers.Serializer):
    category = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()
    essential = serializers.BooleanField()
    channels = NotificationChannelSchema(many=True)


class NotificationPreferencesSchema(serializers.Serializer):
    categories = NotificationCategorySchema(many=True)


class NotificationChoiceInputSchema(serializers.Serializer):
    category = serializers.CharField()
    channel = serializers.CharField()
    enabled = serializers.BooleanField()


class NotificationPreferenceView(WorkspaceLookupMixin, APIView):
    """Only ever the caller's own choices: there is no user in the URL to change."""

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    def answer(self, request):
        return Response({"categories": notifications.describe(request.user, self.get_workspace())})

    @extend_schema(responses=NotificationPreferencesSchema)
    def get(self, request, workspace_public_id):
        return self.answer(request)

    @extend_schema(request=NotificationChoiceInputSchema, responses=NotificationPreferencesSchema)
    def put(self, request, workspace_public_id):
        body = request.data if isinstance(request.data, dict) else {}
        problems = {}
        for field in ("category", "channel"):
            if not isinstance(body.get(field), str):
                problems[field] = ["Send this as text."]
        if not isinstance(body.get("enabled"), bool):
            problems["enabled"] = ["Send true or false."]
        if problems:
            raise ValidationError(problems)
        notifications.set_preference(
            request.user,
            self.get_workspace(),
            body["category"],
            body["channel"],
            body["enabled"],
        )
        return self.answer(request)
