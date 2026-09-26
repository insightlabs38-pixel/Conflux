from rest_framework import serializers

from .models import Action, ExceptionGrant, Policy, PolicyBinding, TemporalGate


class PolicySerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    ast = serializers.JSONField(required=False)
    preset = serializers.CharField(write_only=True, required=False)
    preset_params = serializers.DictField(write_only=True, required=False)

    class Meta:
        model = Policy
        fields = ["public_id", "name", "ast", "preset", "preset_params", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        if not attrs.get("ast") and not attrs.get("preset"):
            raise serializers.ValidationError({"ast": "Provide either 'ast' or 'preset'."})
        return attrs


class TemporalGateSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = TemporalGate
        fields = ["public_id", "name", "opens_at", "closes_at", "created_at"]
        read_only_fields = ["created_at"]


class PolicyBindingSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    policy = serializers.UUIDField()
    action = serializers.ChoiceField(choices=Action.choices)

    class Meta:
        model = PolicyBinding
        fields = ["public_id", "action", "policy", "created_at"]
        read_only_fields = ["created_at"]
        validators = []  # see StageTransitionSerializer for why: UUID vs. FK id

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["policy"] = str(instance.policy.public_id)
        return data


class ExceptionGrantSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    action = serializers.ChoiceField(choices=Action.choices)

    class Meta:
        model = ExceptionGrant
        fields = [
            "public_id",
            "action",
            "subject_type",
            "subject_id",
            "scope",
            "reason",
            "granted_at",
            "expires_at",
        ]
        read_only_fields = ["granted_at"]
