from accounts.models import User
from audit.services import record_mutation
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from events.views import OrganizerView
from projects.models import Project
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .keys import public_key_pem
from .records import (
    ALGORITHM,
    ISSUER,
    RecordVerificationError,
    build_event_record,
    build_judge_record,
    build_project_record,
    sign_record,
    verify_record,
)


class RecordOutput(serializers.Serializer):
    token = serializers.CharField()
    claims = serializers.DictField()


class JudgeRecordInput(serializers.Serializer):
    user = serializers.UUIDField()


class ProjectRecordInput(serializers.Serializer):
    project = serializers.UUIDField()


class RecordBase(OrganizerView):
    def _issue(self, request, event, claims):
        with transaction.atomic():
            token = sign_record(claims)
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="record.issued",
                target=event,
                event_type="record.issued",
                payload={"event": str(event.public_id), "kind": claims["kind"]},
            )
        return Response({"token": token, "claims": claims}, status=201)


class EventRecordView(RecordBase):
    @extend_schema(request=None, responses={201: RecordOutput})
    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        return self._issue(request, event, build_event_record(event))


class ProjectRecordView(RecordBase):
    @extend_schema(request=ProjectRecordInput, responses={201: RecordOutput})
    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        data = ProjectRecordInput(data=request.data)
        data.is_valid(raise_exception=True)
        project = get_object_or_404(Project, event=event, public_id=data.validated_data["project"])
        return self._issue(request, event, build_project_record(project))


class JudgeRecordView(RecordBase):
    @extend_schema(request=JudgeRecordInput, responses={201: RecordOutput})
    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        data = JudgeRecordInput(data=request.data)
        data.is_valid(raise_exception=True)
        user = get_object_or_404(User, public_id=data.validated_data["user"])
        try:
            claims = build_judge_record(user, event)
        except ValueError as exc:
            raise ValidationError({"user": str(exc)}) from exc
        return self._issue(request, event, claims)


class VerificationKeyOutput(serializers.Serializer):
    issuer = serializers.CharField()
    algorithm = serializers.CharField()
    public_key_pem = serializers.CharField()


class VerificationKeyView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=VerificationKeyOutput)
    def get(self, request):
        return Response(
            {"issuer": ISSUER, "algorithm": ALGORITHM, "public_key_pem": public_key_pem()}
        )


class VerifyRecordInput(serializers.Serializer):
    token = serializers.CharField()


class VerifyRecordOutput(serializers.Serializer):
    valid = serializers.BooleanField()
    claims = serializers.DictField(required=False)
    error = serializers.CharField(required=False)


class VerifyRecordView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(request=VerifyRecordInput, responses=VerifyRecordOutput)
    def post(self, request):
        data = VerifyRecordInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            claims = verify_record(data.validated_data["token"])
        except RecordVerificationError as exc:
            return Response({"valid": False, "error": str(exc)})
        return Response({"valid": True, "claims": claims})
