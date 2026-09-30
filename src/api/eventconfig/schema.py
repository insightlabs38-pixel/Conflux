from rest_framework import serializers


class ReadinessFixSchema(serializers.Serializer):
    destination = serializers.CharField()
    section = serializers.CharField(allow_blank=True)


class ReadinessItemSchema(serializers.Serializer):
    id = serializers.CharField()
    severity = serializers.ChoiceField(choices=["blocker", "warning"])
    passed = serializers.BooleanField()
    detail = serializers.CharField()
    module = serializers.CharField()
    fix = ReadinessFixSchema()


class ReadinessSchema(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ready", "warning", "blocked"])
    items = ReadinessItemSchema(many=True)


class ConfigurationLockSchema(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()


class ConfigurationWriteSchema(serializers.Serializer):
    method = serializers.CharField()
    path = serializers.CharField()
    field = serializers.CharField()
    body = serializers.ChoiceField(choices=["partial", "whole"])


class ConfigurationPresetSchema(serializers.Serializer):
    key = serializers.CharField()
    version = serializers.IntegerField()
    label = serializers.CharField()


class ConfigurationEntrySchema(serializers.Serializer):
    key = serializers.CharField()
    module = serializers.CharField()
    tier = serializers.ChoiceField(choices=["base", "advanced", "expert"])
    label = serializers.CharField()
    help = serializers.CharField()
    schema = serializers.JSONField()
    value = serializers.JSONField(allow_null=True)
    default = serializers.JSONField(allow_null=True)
    baseline = serializers.JSONField(allow_null=True)
    source = serializers.ChoiceField(
        choices=["default", "preset", "overridden", "set", "unset", "derived"]
    )
    editable = serializers.BooleanField()
    lock = ConfigurationLockSchema(allow_null=True)
    write = ConfigurationWriteSchema(allow_null=True)
    module_enabled = serializers.BooleanField()


class ConfigurationSchema(serializers.Serializer):
    event = serializers.UUIDField()
    preset = ConfigurationPresetSchema(allow_null=True)
    settings = ConfigurationEntrySchema(many=True)
