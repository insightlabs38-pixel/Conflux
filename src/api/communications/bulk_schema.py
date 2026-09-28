from rest_framework import serializers


class BulkOperationInput(serializers.Serializer):
    action = serializers.ChoiceField(choices=["assign", "advance", "extend", "move", "send"])
    plan = serializers.UUIDField(required=False)
    coverage = serializers.IntegerField(required=False, min_value=1, max_value=100)
    stage = serializers.UUIDField(required=False)
    to_stage = serializers.UUIDField(required=False)
    entries = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=False, max_length=100
    )
    gates = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=False, max_length=100
    )
    seconds = serializers.IntegerField(required=False, min_value=1, max_value=366 * 86400)
    projects = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=False, max_length=100
    )
    track = serializers.UUIDField(required=False)
    subject = serializers.CharField(required=False, max_length=200)
    body = serializers.CharField(required=False, max_length=10000)
    audience_kind = serializers.CharField(required=False, max_length=40)
    audience_params = serializers.DictField(required=False)

    def to_internal_value(self, data):
        if isinstance(data, dict) and data.keys() - self.fields.keys():
            raise serializers.ValidationError("Unknown operation fields.")
        return super().to_internal_value(data)

    def validate(self, attrs):
        required = {
            "assign": {"plan", "coverage"},
            "advance": {"stage", "to_stage", "entries"},
            "extend": {"gates", "seconds"},
            "move": {"projects", "track"},
            "send": {"subject", "body", "audience_kind"},
        }[attrs["action"]]
        allowed = required | {"action"}
        if attrs["action"] == "send":
            allowed.add("audience_params")
        if required - attrs.keys() or attrs.keys() - allowed:
            raise serializers.ValidationError("Supply exactly the fields for this action.")
        for field in ("entries", "gates", "projects"):
            if field in attrs and len(set(attrs[field])) != len(attrs[field]):
                raise serializers.ValidationError({field: "Duplicate targets are not allowed."})
        return attrs


class BulkRequest(serializers.Serializer):
    operations = BulkOperationInput(many=True, allow_empty=False, max_length=20)
    preview_token = serializers.CharField(required=False, max_length=4096)

    def validate(self, attrs):
        if self.initial_data.keys() - {"operations", "preview_token"}:
            raise serializers.ValidationError("Unknown request fields.")
        plans = [op["plan"] for op in attrs["operations"] if op["action"] == "assign"]
        if len(set(plans)) != len(plans):
            raise serializers.ValidationError("Assign each plan at most once per batch.")
        return attrs


class BulkResponse(serializers.Serializer):
    applied = serializers.BooleanField()
    effects = serializers.ListField(child=serializers.JSONField())
    preview_token = serializers.CharField(required=False)
    expires_in = serializers.IntegerField(required=False)
