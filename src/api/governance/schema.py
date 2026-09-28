from rest_framework import serializers


class SettingsInput(serializers.Serializer):
    require_publication_approval = serializers.BooleanField()


class ParticipantRulesInput(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    body = serializers.CharField()


class RulesAcknowledgeInput(serializers.Serializer):
    number = serializers.IntegerField(required=False)


class PublicationRequestInput(serializers.Serializer):
    plan = serializers.UUIDField()
    normalization_run = serializers.UUIDField()
    tie_breaks = serializers.DictField(child=serializers.IntegerField(), required=False)
    reason = serializers.CharField(required=False, allow_blank=True)


class DecisionNoteInput(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)


class AssignmentResponseInput(serializers.Serializer):
    status = serializers.ChoiceField(choices=["accepted", "declined"])
    reason = serializers.CharField(required=False, allow_blank=True)


class ExceptionRequestInput(serializers.Serializer):
    reason = serializers.CharField()


class ExceptionApprovalInput(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)
    expires_at = serializers.DateTimeField(required=False)


class MaintenanceInput(serializers.Serializer):
    read_only = serializers.BooleanField()
    message = serializers.CharField(max_length=300, required=False, allow_blank=True)


class VisibilityInput(serializers.Serializer):
    gallery_visible = serializers.BooleanField(required=False)
    blocked = serializers.BooleanField(required=False)
    reason = serializers.CharField(max_length=300, required=False, allow_blank=True)


class CsvPreviewInput(serializers.Serializer):
    csv_text = serializers.CharField()
    mapping = serializers.DictField(child=serializers.CharField(), required=False)
