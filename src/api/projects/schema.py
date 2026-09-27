from rest_framework import serializers


class ProjectCreateInputSchema(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    team = serializers.UUIDField(required=False, allow_null=True)
    track = serializers.UUIDField(required=False, allow_null=True)


class ProjectPatchInputSchema(serializers.Serializer):
    name = serializers.CharField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    track = serializers.UUIDField(required=False, allow_null=True)


class SubmissionVersionSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    number = serializers.IntegerField()
    digest = serializers.CharField()
    finalized_at = serializers.DateTimeField()
    finalized_by = serializers.UUIDField()


class SubmissionSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    stage = serializers.UUIDField()
    status = serializers.CharField()
    draft_payload = serializers.JSONField()
    draft_revision = serializers.IntegerField()
    current_version = serializers.UUIDField(allow_null=True)
    versions = SubmissionVersionSchema(many=True)


class SubmissionStageSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    name = serializers.CharField()
    submission = SubmissionSchema(allow_null=True)


class SubmissionDraftInputSchema(serializers.Serializer):
    draft_payload = serializers.JSONField()
    draft_revision = serializers.IntegerField()


class SubmissionFinalizeInputSchema(serializers.Serializer):
    draft_revision = serializers.IntegerField()


class SubmissionReceiptSchema(serializers.Serializer):
    submission = SubmissionSchema()
    receipt = serializers.UUIDField()


class SubmissionReopenInputSchema(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class SubmissionDiffSchema(serializers.Serializer):
    from_version = serializers.IntegerField()
    to_version = serializers.IntegerField()
    diff = serializers.JSONField()
