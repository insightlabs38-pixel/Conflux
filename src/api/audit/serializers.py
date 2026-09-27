from rest_framework import serializers


class AuditEventSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    actor = serializers.CharField(allow_null=True)
    action = serializers.CharField()
    target_type = serializers.CharField(allow_blank=True)
    target_id = serializers.CharField(allow_blank=True)
    metadata = serializers.JSONField()
    created_at = serializers.DateTimeField()
