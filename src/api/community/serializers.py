from django.core.exceptions import ValidationError as ModelValidationError
from rest_framework import serializers

from .models import Comment, VoteToken, VotingPlan


class VotingPlanSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = VotingPlan
        fields = [
            "public_id",
            "identity_mode",
            "opens_at",
            "closes_at",
            "allow_comments",
            "comment_visibility",
            "results_published_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["results_published_at", "created_at", "updated_at"]

    def validate(self, attrs):
        opens_at = attrs.get("opens_at", getattr(self.instance, "opens_at", None))
        closes_at = attrs.get("closes_at", getattr(self.instance, "closes_at", None))
        if opens_at and closes_at and opens_at >= closes_at:
            raise serializers.ValidationError({"closes_at": "Must be after opens_at."})
        return attrs


class VoteTokenSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = VoteToken
        fields = ["public_id", "token", "redeemed_at", "created_at"]


class CommentSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    author = serializers.UUIDField(source="author.public_id", read_only=True)

    class Meta:
        model = Comment
        fields = ["public_id", "author", "body", "created_at", "hidden_at"]
        read_only_fields = ["created_at", "hidden_at"]

    def validate_body(self, value):
        try:
            Comment(body=value).clean()
        except ModelValidationError as exc:
            raise serializers.ValidationError(exc.message_dict.get("body", exc.messages)) from exc
        return value


class VotingStatusSchema(serializers.Serializer):
    identity_mode = serializers.CharField()
    opens_at = serializers.DateTimeField()
    closes_at = serializers.DateTimeField()
    is_open = serializers.BooleanField()
    allow_comments = serializers.BooleanField()


class CandidateSchema(serializers.Serializer):
    project = serializers.UUIDField()
    name = serializers.CharField()


class VoteInputSchema(serializers.Serializer):
    project = serializers.UUIDField()
    token = serializers.CharField(required=False)


class VoteReceiptSchema(serializers.Serializer):
    public_id = serializers.UUIDField()


class EmailTokenInputSchema(serializers.Serializer):
    email = serializers.EmailField()


class EmailTokenReceiptSchema(serializers.Serializer):
    token = serializers.CharField()
    expires_at = serializers.DateTimeField()


class VotingResultSchema(serializers.Serializer):
    project = serializers.UUIDField()
    name = serializers.CharField()
    votes = serializers.IntegerField()


class AbuseSignalSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    signal_type = serializers.CharField()
    detail = serializers.CharField()
    evidence = serializers.JSONField()
    occurred_at = serializers.DateTimeField()
    resolved_at = serializers.DateTimeField(allow_null=True)
    resolved_by = serializers.UUIDField(allow_null=True)
    resolution_note = serializers.CharField(allow_blank=True)


class ResolutionInputSchema(serializers.Serializer):
    resolution_note = serializers.CharField(min_length=1, max_length=2000)


class CommunityAuditSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    actor = serializers.CharField(allow_null=True)
    action = serializers.CharField()
    detail = serializers.CharField()
    created_at = serializers.DateTimeField()
