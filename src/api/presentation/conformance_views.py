from django.utils import timezone
from drf_spectacular.utils import extend_schema
from events.views import OrganizerView
from rest_framework import serializers
from rest_framework.response import Response

from .conformance import build_conformance_report


class ConformanceReportOutput(serializers.Serializer):
    event = serializers.UUIDField()
    generated_at = serializers.DateTimeField()
    conformance_claimed = serializers.BooleanField()
    standard = serializers.CharField()
    theme = serializers.DictField()
    summary = serializers.DictField(child=serializers.IntegerField())
    pages = serializers.ListField(child=serializers.DictField())
    manual_review = serializers.ListField(child=serializers.DictField())


class ConformanceReportView(OrganizerView):
    @extend_schema(responses=ConformanceReportOutput)
    def get(self, request, workspace_public_id, event_public_id):
        return Response(build_conformance_report(self.get_event(), now=timezone.now()))
