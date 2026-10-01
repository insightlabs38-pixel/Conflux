from rest_framework import serializers

from .bulk import ACTIONS


class RegisteredActionField(serializers.ChoiceField):
    """The five built-in actions are the documented enum; an action registered by another app
    (`bulk.register_action`) is accepted too, so the planner can be extended without editing it."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data in ACTIONS:
            return data
        return super().to_internal_value(data)


class BulkOperationInput(serializers.Serializer):
    action = RegisteredActionField(choices=["assign", "advance", "extend", "move", "send"])
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
    params = serializers.DictField(
        required=False, help_text="Fields of an action registered by another app."
    )

    def to_internal_value(self, data):
        if isinstance(data, dict) and data.keys() - self.fields.keys():
            raise serializers.ValidationError("Unknown operation fields.")
        return super().to_internal_value(data)

    def validate(self, attrs):
        action = ACTIONS[attrs["action"]]
        if action.params is not None:
            if attrs.keys() - {"action", "params"} or "params" not in attrs:
                raise serializers.ValidationError("Supply the action and its params object.")
            checked = action.params(data=attrs["params"])
            checked.is_valid(raise_exception=True)
            return {"action": attrs["action"], "params": dict(checked.validated_data)}
        allowed = action.required | action.optional | {"action"}
        if action.required - attrs.keys() or attrs.keys() - allowed:
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
    approvals = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Approvals the apply will need first (a preview only).",
    )


class BulkReceiptSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    actor = serializers.CharField()
    created_at = serializers.DateTimeField()
    actions = serializers.ListField(child=serializers.CharField())
    effects = serializers.ListField(child=serializers.JSONField())
