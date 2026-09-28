from drf_spectacular.utils import OpenApiParameter, extend_schema
from events.views import OrganizerView
from rest_framework import serializers
from rest_framework.response import Response

from .analytics import compute_analytics


class EventAnalyticsResponse(serializers.Serializer):
    event = serializers.UUIDField()
    generated_at = serializers.DateTimeField()
    registration = serializers.JSONField()
    teams = serializers.JSONField()
    submissions = serializers.JSONField()
    judging = serializers.JSONField()
    voting = serializers.JSONField()


class EventAnalyticsQuery(serializers.Serializer):
    plan_offset = serializers.IntegerField(default=0, min_value=0, max_value=1000000)


class EventAnalyticsView(OrganizerView):
    @extend_schema(
        parameters=[OpenApiParameter("plan_offset", int)], responses=EventAnalyticsResponse
    )
    def get(self, request, workspace_public_id, event_public_id):
        query = EventAnalyticsQuery(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response(compute_analytics(self.get_event(), **query.validated_data))
