from rest_framework import serializers


class AuditEventSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    actor = serializers.CharField(allow_null=True)
    action = serializers.CharField()
    target_type = serializers.CharField(allow_blank=True)
    target_id = serializers.CharField(allow_blank=True)
    metadata = serializers.JSONField()
    created_at = serializers.DateTimeField()


class ConfigHistoryEntrySchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    actor = serializers.CharField(allow_null=True)
    action = serializers.CharField()
    resource_type = serializers.CharField(allow_blank=True)
    resource_id = serializers.CharField(allow_blank=True)
    changes = serializers.JSONField()
    diff = serializers.JSONField(
        help_text="Per changed field, the structural or text diff of its before and after "
        "(`core.version_diff`)."
    )
    created_at = serializers.DateTimeField()


class ConfigRestoreResultSchema(serializers.Serializer):
    restored = serializers.BooleanField()
    resource_type = serializers.CharField()
    resource_id = serializers.CharField()
    changes = serializers.JSONField()
