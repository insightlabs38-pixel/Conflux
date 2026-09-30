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
    constraint = serializers.CharField(allow_null=True)
    write = ConfigurationWriteSchema(allow_null=True)
    module_enabled = serializers.BooleanField()


class ConfigurationSchema(serializers.Serializer):
    event = serializers.UUIDField()
    preset = ConfigurationPresetSchema(allow_null=True)
    settings = ConfigurationEntrySchema(many=True)


class WorkflowDifferenceSchema(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()


class WorkflowSchema(serializers.Serializer):
    source = serializers.ChoiceField(choices=["preset", "custom", "none"])
    preset = ConfigurationPresetSchema(allow_null=True)
    stages = serializers.ListField(child=serializers.CharField())
    differences = WorkflowDifferenceSchema(many=True)


class GeneratedValueSchema(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    value = serializers.JSONField(allow_null=True)


class GeneratedExplicitSchema(GeneratedValueSchema):
    reason = serializers.ChoiceField(choices=["changed", "organizer"])
    baseline = serializers.JSONField(allow_null=True)
    # Where the baseline comes from: the format, or the registry default when there is none.
    origin = serializers.ChoiceField(choices=["preset", "default"])
    write = ConfigurationWriteSchema(allow_null=True)


class GeneratedInheritedSchema(GeneratedValueSchema):
    origin = serializers.ChoiceField(choices=["preset", "default"])


class GeneratedDocumentSchema(serializers.Serializer):
    format = serializers.CharField(allow_null=True)
    settings = serializers.JSONField()


class GeneratedConfigurationSchema(serializers.Serializer):
    event = serializers.UUIDField()
    preset = ConfigurationPresetSchema(allow_null=True)
    explicit = GeneratedExplicitSchema(many=True)
    inherited = GeneratedInheritedSchema(many=True)
    derived = GeneratedValueSchema(many=True)
    unset = serializers.ListField(child=serializers.CharField())
    document = GeneratedDocumentSchema()
    text = serializers.CharField()


class ConsequenceItemSchema(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    count = serializers.IntegerField(allow_null=True)


class ConsequenceTargetSchema(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField(allow_blank=True)


class ConsequencesSchema(serializers.Serializer):
    action = serializers.CharField()
    title = serializers.CharField()
    target = ConsequenceTargetSchema(allow_null=True)
    allowed = serializers.BooleanField()
    refusal = ConsequenceItemSchema(allow_null=True)
    blockers = ConsequenceItemSchema(many=True)
    consequences = ConsequenceItemSchema(many=True)
    reversible = serializers.BooleanField()
    severity = serializers.ChoiceField(choices=["medium", "high"])
    confirm_label = serializers.CharField()
