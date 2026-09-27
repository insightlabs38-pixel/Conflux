from rest_framework import serializers


class OperationsSummarySchema(serializers.Serializer):
    participants = serializers.JSONField()
    submissions = serializers.JSONField()
    judging = serializers.JSONField()
    stages = serializers.JSONField()
    publication = serializers.JSONField()
    moderation = serializers.JSONField()


class ChecklistItemSchema(serializers.Serializer):
    id = serializers.CharField()
    severity = serializers.CharField()
    passed = serializers.BooleanField()
    detail = serializers.CharField()


class LaunchChecklistSchema(serializers.Serializer):
    status = serializers.CharField()
    items = ChecklistItemSchema(many=True)


class OperatorEventSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    name = serializers.CharField()
    status = serializers.CharField()
    is_public = serializers.BooleanField()
    updated_at = serializers.DateTimeField()
    health = serializers.CharField()
    blocker_count = serializers.IntegerField()
    warning_count = serializers.IntegerField()


class OperatorTemplateSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    name = serializers.CharField()
    source_event_name = serializers.CharField()


class OperatorActivitySchema(serializers.Serializer):
    action = serializers.CharField()
    actor = serializers.CharField(allow_null=True)
    target_type = serializers.CharField()
    target_id = serializers.CharField()
    created_at = serializers.DateTimeField()


class OperatorConsoleSchema(serializers.Serializer):
    event_total = serializers.IntegerField()
    events = OperatorEventSchema(many=True)
    template_total = serializers.IntegerField()
    templates = OperatorTemplateSchema(many=True)
    activity = OperatorActivitySchema(many=True)


class AudienceKindSchema(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    param_names = serializers.ListField(child=serializers.CharField())
    options = serializers.JSONField()


class AudiencePreviewInputSchema(serializers.Serializer):
    audience_kind = serializers.CharField()
    audience_params = serializers.JSONField(required=False)


class AudienceMemberSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    username = serializers.CharField()


class AudiencePreviewSchema(serializers.Serializer):
    count = serializers.IntegerField()
    sample = AudienceMemberSchema(many=True)


class MessageInputSchema(serializers.Serializer):
    subject = serializers.CharField(max_length=200)
    body = serializers.CharField()
    audience_kind = serializers.CharField()
    audience_params = serializers.JSONField(required=False)


class MessageSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    subject = serializers.CharField()
    body = serializers.CharField()
    audience_kind = serializers.CharField()
    audience_params = serializers.JSONField()
    recipient_count = serializers.IntegerField()
    email_failure_count = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class ReminderInputSchema(serializers.Serializer):
    kind = serializers.ChoiceField(choices=["deadline", "judging", "voting"])
    due_at = serializers.DateTimeField()
    audience_kind = serializers.CharField(max_length=40)
    audience_params = serializers.DictField(child=serializers.CharField(), required=False)
    subject = serializers.CharField(max_length=200)
    body = serializers.CharField()


class ReminderSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    kind = serializers.CharField()
    due_at = serializers.DateTimeField()
    audience_kind = serializers.CharField()
    audience_params = serializers.JSONField()
    subject = serializers.CharField()
    body = serializers.CharField()
    status = serializers.CharField()
    sent_message = serializers.UUIDField(allow_null=True)
    cancelled_at = serializers.DateTimeField(allow_null=True)
    last_error = serializers.CharField()


class InboxMessageSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    subject = serializers.CharField()
    body = serializers.CharField()
    event = serializers.UUIDField()
    event_name = serializers.CharField()
    created_at = serializers.DateTimeField()
    read_at = serializers.DateTimeField(allow_null=True)
