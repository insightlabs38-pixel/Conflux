from rest_framework import serializers

from .serializers import BasePrizeSerializer, EventSerializer, TrackSerializer


class EventDashboardSchema(serializers.Serializer):
    event = EventSerializer()
    track_count = serializers.IntegerField()
    base_prize_count = serializers.IntegerField()
    configuration_checks = serializers.ListField(child=serializers.CharField())


class PublicEventSchema(serializers.Serializer):
    presentation = serializers.JSONField()
    public_id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.SlugField()
    description = serializers.CharField(allow_blank=True)
    timezone = serializers.CharField()
    starts_at = serializers.DateTimeField(allow_null=True)
    ends_at = serializers.DateTimeField(allow_null=True)
    status = serializers.CharField()
    tracks = TrackSerializer(many=True)
    base_prizes = BasePrizeSerializer(many=True)
