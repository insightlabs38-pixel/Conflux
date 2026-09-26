from rest_framework import serializers

from .models import ParticipationMode, Stage, StageTransition


class StageSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    participation_mode = serializers.ChoiceField(choices=ParticipationMode.choices, required=False)

    class Meta:
        model = Stage
        fields = [
            "public_id",
            "name",
            "position",
            "is_initial",
            "participation_mode",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class StageTransitionSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    from_stage = serializers.UUIDField()
    to_stage = serializers.UUIDField()

    class Meta:
        model = StageTransition
        fields = ["public_id", "from_stage", "to_stage", "created_at"]
        read_only_fields = ["created_at"]
        # `from_stage`/`to_stage` are overridden to accept public_id UUIDs
        # rather than the model's real (integer) FK ids, so DRF's
        # auto-generated UniqueTogetherValidator for `unique_stage_transition`
        # would filter the wrong column type. The view's IntegrityError
        # handling on save() enforces that constraint instead.
        validators = []

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["from_stage"] = str(instance.from_stage.public_id)
        data["to_stage"] = str(instance.to_stage.public_id)
        return data
