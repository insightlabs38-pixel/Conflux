from rest_framework import serializers


class ValidationSchema(serializers.Serializer):
    outcome = serializers.CharField()
    detail = serializers.CharField()


class ArtifactSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    kind = serializers.CharField()
    visibility = serializers.CharField()
    title = serializers.CharField()
    external_url = serializers.URLField(allow_blank=True)
    content_type = serializers.CharField(allow_blank=True)
    byte_size = serializers.IntegerField(allow_null=True)
    status = serializers.CharField()
    validation = ValidationSchema(allow_null=True)
    download_url = serializers.URLField(required=False)


class ExternalArtifactInputSchema(serializers.Serializer):
    kind = serializers.CharField()
    visibility = serializers.CharField()
    title = serializers.CharField(required=False)
    external_url = serializers.URLField()


class UploadIntentInputSchema(serializers.Serializer):
    kind = serializers.CharField()
    visibility = serializers.CharField()
    title = serializers.CharField(required=False)
    byte_size = serializers.IntegerField(min_value=0)
    content_type = serializers.CharField()


class UploadIntentSchema(serializers.Serializer):
    artifact = ArtifactSchema()
    intent = serializers.UUIDField()
    expires_at = serializers.DateTimeField()
    upload = serializers.JSONField()


class UploadCompleteInputSchema(serializers.Serializer):
    parts = serializers.JSONField(required=False)


class PreflightCheckSchema(serializers.Serializer):
    code = serializers.CharField()
    severity = serializers.CharField()
    detail = serializers.CharField()


class PreflightSchema(serializers.Serializer):
    status = serializers.CharField()
    checks = PreflightCheckSchema(many=True)
