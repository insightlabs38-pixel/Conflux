from rest_framework import serializers


class GraphValidationSchema(serializers.Serializer):
    valid = serializers.BooleanField()
    order = serializers.ListField(child=serializers.UUIDField(), required=False)
    errors = serializers.ListField(child=serializers.CharField(), required=False)


class AdvancementStrategiesSchema(serializers.Serializer):
    strategies = serializers.ListField(child=serializers.CharField())


class AdvancementCandidateSchema(serializers.Serializer):
    subject_type = serializers.CharField()
    subject_id = serializers.CharField()
    score = serializers.FloatField(required=False, allow_null=True)
    track_id = serializers.CharField(required=False, allow_null=True)


class AdvancementInputSchema(serializers.Serializer):
    to_stage = serializers.UUIDField()
    strategy = serializers.CharField()
    params = serializers.JSONField(required=False)
    candidates = AdvancementCandidateSchema(many=True)


class AdvancementResultSchema(serializers.Serializer):
    class AdvancedSubjectSchema(serializers.Serializer):
        subject_type = serializers.CharField()
        subject_id = serializers.CharField()

    advanced = AdvancedSubjectSchema(many=True)


class AdvancementEvidenceSchema(serializers.Serializer):
    created_at = serializers.DateTimeField()
    actor = serializers.CharField(allow_null=True)
    stage_public_id = serializers.CharField()
    metadata = serializers.JSONField()
