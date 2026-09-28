from accounts.models import User
from audit.services import diff_snapshots, record_mutation, snapshot_fields
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from events.models import Event
from events.views import OrganizerView
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from .models import EventRetentionPolicy
from .privacy import enforce_retention, erase_subject, export_subject, subject_exists

POLICY_FIELDS = ["participant_data_days", "private_artifact_days"]
MAX_DAYS = 36500


class RetentionPolicyInput(serializers.Serializer):
    participant_data_days = serializers.IntegerField(
        min_value=0, max_value=MAX_DAYS, allow_null=True
    )
    private_artifact_days = serializers.IntegerField(
        min_value=0, max_value=MAX_DAYS, allow_null=True
    )

    def validate(self, attrs):
        if self.initial_data.keys() - self.fields.keys():
            raise ValidationError("Unknown fields.")
        return attrs


class RetentionPolicyOutput(serializers.Serializer):
    participant_data_days = serializers.IntegerField(allow_null=True)
    private_artifact_days = serializers.IntegerField(allow_null=True)
    updated_at = serializers.DateTimeField(allow_null=True)


class PrivacyApplyInput(serializers.Serializer):
    apply = serializers.BooleanField(default=False)

    def validate(self, attrs):
        if self.initial_data.keys() - self.fields.keys():
            raise ValidationError("Unknown fields.")
        return attrs


class PrivacyReportOutput(serializers.Serializer):
    applied = serializers.BooleanField()
    erased = serializers.DictField()
    retained = serializers.DictField(required=False)
    retained_reason = serializers.CharField(required=False)
    due = serializers.DictField(required=False)


class SubjectExportOutput(serializers.Serializer):
    subject = serializers.DictField()
    event = serializers.UUIDField()
    data = serializers.DictField()
    retained_data = serializers.DictField()
    artifacts = serializers.ListField(child=serializers.DictField())


class RetentionPolicyView(OrganizerView):
    def render(self, policy):
        return Response(
            RetentionPolicyOutput(
                policy
                or {
                    "participant_data_days": None,
                    "private_artifact_days": None,
                    "updated_at": None,
                }
            ).data
        )

    @extend_schema(responses=RetentionPolicyOutput)
    def get(self, request, workspace_public_id, event_public_id):
        return self.render(EventRetentionPolicy.objects.filter(event=self.get_event()).first())

    @extend_schema(request=RetentionPolicyInput, responses=RetentionPolicyOutput)
    def put(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        data = RetentionPolicyInput(data=request.data)
        data.is_valid(raise_exception=True)
        with transaction.atomic():
            Event.objects.select_for_update().get(pk=event.pk)
            policy = EventRetentionPolicy.objects.filter(event=event).first()
            before = snapshot_fields(policy, POLICY_FIELDS) if policy else None
            policy, _ = EventRetentionPolicy.objects.update_or_create(
                event=event, defaults={**data.validated_data, "updated_by": request.user}
            )
            after = snapshot_fields(policy, POLICY_FIELDS)
            record_mutation(
                actor=request.user,
                workspace=event.workspace,
                action="privacy.retention_policy_saved",
                target=policy,
                metadata={
                    "event_id": str(event.public_id),
                    "changes": diff_snapshots(before, after) if before else after,
                },
            )
        return self.render(policy)


class SubjectView(OrganizerView):
    def get_subject(self, event):
        user = get_object_or_404(User, public_id=self.kwargs["user_public_id"])
        if not subject_exists(event, user):
            raise NotFound("This person has no data in this event.")
        return user


class SubjectExportView(SubjectView):
    @extend_schema(request=None, responses=SubjectExportOutput)
    def post(self, request, workspace_public_id, event_public_id, user_public_id):
        event = self.get_event()
        return Response(export_subject(event, self.get_subject(event), actor=request.user))


class SubjectErasureView(SubjectView):
    @extend_schema(request=PrivacyApplyInput, responses=PrivacyReportOutput)
    def post(self, request, workspace_public_id, event_public_id, user_public_id):
        event = self.get_event()
        data = PrivacyApplyInput(data=request.data)
        data.is_valid(raise_exception=True)
        subject = self.get_subject(event)
        return Response(
            erase_subject(event, subject, actor=request.user, apply=data.validated_data["apply"])
        )


class RetentionRunView(OrganizerView):
    @extend_schema(request=PrivacyApplyInput, responses=PrivacyReportOutput)
    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        data = PrivacyApplyInput(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(
            enforce_retention(
                event, timezone.now(), actor=request.user, apply=data.validated_data["apply"]
            )
        )
