from accounts.authentication import CookieSessionAuthentication
from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import registration
from .models import Event, EventApplication, RegistrationInviteCode
from .serializers import (
    ApplicationDecisionInputSchema,
    ApplyToEventInputSchema,
    EventApplicationSerializer,
    MyEventApplicationResponse,
    RegistrationInviteCodeSerializer,
    RegistrationSettingsSerializer,
)
from .views import OrganizerView


def _validation_error(exc):
    return ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


class RegistrationSettingsView(OrganizerView):
    @extend_schema(responses=RegistrationSettingsSerializer)
    def get(self, request, workspace_public_id, event_public_id):
        settings_obj = registration.get_settings(self.get_event())
        return Response(RegistrationSettingsSerializer(settings_obj).data)

    @extend_schema(request=RegistrationSettingsSerializer, responses=RegistrationSettingsSerializer)
    def put(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        self.ensure_mutable(event)
        settings_obj = registration.get_settings(event)
        serializer = RegistrationSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            for key, value in serializer.validated_data.items():
                setattr(settings_obj, key, value)
            settings_obj.full_clean()
            settings_obj.save()
        except ModelValidationError as exc:
            raise _validation_error(exc) from exc
        return Response(RegistrationSettingsSerializer(settings_obj).data)


class RegistrationInviteCodeListView(OrganizerView):
    @extend_schema(responses=RegistrationInviteCodeSerializer(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        codes = RegistrationInviteCode.objects.filter(event=self.get_event()).order_by(
            "-created_at", "-id"
        )
        return Response(RegistrationInviteCodeSerializer(codes, many=True).data)

    @extend_schema(
        request=RegistrationInviteCodeSerializer, responses={201: RegistrationInviteCodeSerializer}
    )
    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        self.ensure_mutable(event)
        serializer = RegistrationInviteCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        max_uses = serializer.validated_data.get("max_uses", 1)
        try:
            invite = registration.create_invite_code(event, request.user, max_uses=max_uses)
        except ModelValidationError as exc:
            raise _validation_error(exc) from exc
        return Response(RegistrationInviteCodeSerializer(invite).data, status=201)


class RegistrationInviteCodeDetailView(OrganizerView):
    @extend_schema(responses={204: None})
    def delete(self, request, workspace_public_id, event_public_id, code_public_id):
        event = self.get_event()
        self.ensure_mutable(event)
        invite = get_object_or_404(RegistrationInviteCode, event=event, public_id=code_public_id)
        registration.revoke_invite_code(invite)
        return Response(status=204)


class EventApplicationListView(OrganizerView):
    @extend_schema(responses=EventApplicationSerializer(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        applications = (
            EventApplication.objects.filter(event=self.get_event())
            .select_related("user", "decided_by")
            .order_by("waitlist_position", "created_at", "id")
        )
        status_filter = request.query_params.get("status")
        if status_filter:
            applications = applications.filter(status=status_filter)
        return Response(EventApplicationSerializer(applications, many=True).data)


class EventApplicationDecisionView(OrganizerView):
    @extend_schema(request=ApplicationDecisionInputSchema, responses=EventApplicationSerializer)
    def post(self, request, workspace_public_id, event_public_id, application_public_id):
        serializer = ApplicationDecisionInputSchema(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = get_object_or_404(
            EventApplication, event=self.get_event(), public_id=application_public_id
        )
        try:
            application = registration.decide_application(
                application, serializer.validated_data["decision"], actor=request.user
            )
        except ModelValidationError as exc:
            raise _validation_error(exc) from exc
        return Response(EventApplicationSerializer(application).data)


class MyEventApplicationView(APIView):
    """Self-serve: any authenticated user, whether or not they already hold
    a workspace membership, can check or submit their own application --
    unlike every other event-scoped view here, membership is exactly what
    this endpoint exists to grant, so it can't be a precondition of it.
    """

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_event(self):
        return get_object_or_404(
            Event,
            workspace__public_id=self.kwargs["workspace_public_id"],
            public_id=self.kwargs["event_public_id"],
        )

    @extend_schema(responses=MyEventApplicationResponse)
    def get(self, request, workspace_public_id, event_public_id):
        application = EventApplication.objects.filter(
            event=self.get_event(), user=request.user
        ).first()
        return Response(
            {"application": EventApplicationSerializer(application).data if application else None}
        )

    @extend_schema(request=ApplyToEventInputSchema, responses={201: EventApplicationSerializer})
    def post(self, request, workspace_public_id, event_public_id):
        serializer = ApplyToEventInputSchema(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            application = registration.apply_to_event(
                self.get_event(),
                request.user,
                note=data.get("note", ""),
                code=data.get("code") or None,
            )
        except ModelValidationError as exc:
            raise _validation_error(exc) from exc
        return Response(EventApplicationSerializer(application).data, status=201)
