from rest_framework import serializers

from .models import Action, ExceptionGrant, Policy, PolicyBinding, TemporalGate
from .timezone_safety import dst_warning, local_iso


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
        if not attrs.get("ast", getattr(self.instance, "ast", None)) and not attrs.get("preset"):
            raise serializers.ValidationError({"ast": "Provide either 'ast' or 'preset'."})
        return attrs


class TemporalGateSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    # VS24: per-user/organizer display safeguards -- `opens_at`/`closes_at`
    # stay the canonical UTC instants (writable, unchanged); these three
    # are read-only presentation aids computed from the event's declared
    # timezone, never persisted.
    event_local_opens_at = serializers.SerializerMethodField()
    event_local_closes_at = serializers.SerializerMethodField()
    dst_warning = serializers.SerializerMethodField()

    class Meta:
        model = TemporalGate
        fields = [
            "public_id",
            "name",
            "opens_at",
            "closes_at",
            "event_local_opens_at",
            "event_local_closes_at",
            "dst_warning",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def get_event_local_opens_at(self, obj) -> str | None:
        return local_iso(obj.opens_at, obj.event.timezone)

    def get_event_local_closes_at(self, obj) -> str | None:
        return local_iso(obj.closes_at, obj.event.timezone)

    def get_dst_warning(self, obj) -> str | None:
        return dst_warning(obj.opens_at, obj.closes_at, obj.event.timezone)


class TimelineWindowSchema(serializers.Serializer):
    """One named window (the event itself, or a `TemporalGate`) on the
    organizer's UTC canonical timeline (VS24) -- `opens_at`/`closes_at` are
    the authoritative UTC instants; the rest are presentation aids.
    """

    label = serializers.CharField()
    opens_at = serializers.DateTimeField(allow_null=True)
    closes_at = serializers.DateTimeField(allow_null=True)
    event_local_opens_at = serializers.CharField(allow_null=True)
    event_local_closes_at = serializers.CharField(allow_null=True)
    dst_warning = serializers.CharField(allow_null=True)


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
