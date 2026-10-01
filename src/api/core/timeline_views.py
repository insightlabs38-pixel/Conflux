"""The timeline endpoint (PD-F002-B01-T08): derived, read-only, organizer-facing."""

from accounts.authentication import CookieSessionAuthentication
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import OpenApiParameter, extend_schema
from events.models import Event
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role

from . import timeline
from .mixins import WorkspaceLookupMixin
from .permissions import require_roles


class TimelineWriteSchema(serializers.Serializer):
    method = serializers.CharField()
    path = serializers.CharField()
    fields = serializers.DictField(child=serializers.CharField())
    extra = serializers.DictField()


class TimelineItemSchema(serializers.Serializer):
    kind = serializers.CharField()
    kind_label = serializers.CharField()
    key = serializers.CharField()
    label = serializers.CharField()
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField(allow_null=True)
    local_starts_at = serializers.CharField()
    local_ends_at = serializers.CharField(allow_null=True)
    dst_note = serializers.CharField(allow_null=True)
    source = serializers.DictField()
    editable = serializers.BooleanField()
    write = TimelineWriteSchema(allow_null=True)
    note = serializers.CharField(allow_blank=True)


class TimelineConflictSchema(serializers.Serializer):
    code = serializers.CharField()
    severity = serializers.ChoiceField(choices=["advisory"])
    message = serializers.CharField()
    items = serializers.ListField(child=serializers.CharField())


class TimelineSchema(serializers.Serializer):
    event = serializers.UUIDField()
    timezone = serializers.CharField()
    total = serializers.IntegerField()
    items = TimelineItemSchema(many=True)
    conflicts = TimelineConflictSchema(many=True)


def _instant(request, name):
    raw = request.query_params.get(name)
    if not raw:
        return None
    value = parse_datetime(raw.replace(" ", "+")) if isinstance(raw, str) else None
    if value is None or timezone.is_naive(value):
        raise ValidationError({name: ["Use an ISO 8601 time with a UTC offset, e.g. ...Z."]})
    return value


class TimelineView(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(
        parameters=[
            OpenApiParameter("from", str, description="Only items ending at or after this time."),
            OpenApiParameter("to", str, description="Only items starting at or before this time."),
            OpenApiParameter("kinds", str, description="Comma list of kinds to include."),
            OpenApiParameter("limit", int, description="1-500, default 200."),
        ],
        responses=TimelineSchema,
    )
    def get(self, request, workspace_public_id, event_public_id):
        event = get_object_or_404(Event, workspace=self.get_workspace(), public_id=event_public_id)
        start, end = _instant(request, "from"), _instant(request, "to")
        if start and end and end < start:
            raise ValidationError({"to": ["`to` must not be before `from`."]})
        raw_kinds = request.query_params.get("kinds")
        kinds = {k for k in raw_kinds.split(",") if k} if raw_kinds else None
        try:
            limit = int(request.query_params.get("limit", 200))
        except ValueError as exc:
            raise ValidationError({"limit": ["Must be an integer."]}) from exc
        if not 1 <= limit <= timeline.MAX_ITEMS:
            raise ValidationError({"limit": [f"Must be between 1 and {timeline.MAX_ITEMS}."]})
        try:
            return Response(timeline.build(event, start=start, end=end, kinds=kinds, limit=limit))
        except ValueError as exc:
            raise ValidationError({"kinds": [str(exc)]}) from exc
