from audit.services import record_mutation
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from events.models import Track
from events.views import OrganizerView
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import AgendaSession, Location
from .views import StrictInput


class SessionInput(StrictInput):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(max_length=2000, allow_blank=True, required=False)
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField()
    location = serializers.UUIDField(allow_null=True, required=False)
    track = serializers.UUIDField(allow_null=True, required=False)
    speakers = serializers.CharField(max_length=300, allow_blank=True, required=False)
    stream_url = serializers.CharField(max_length=200, allow_blank=True, required=False)
    is_public = serializers.BooleanField(required=False)


class SessionPatchInput(SessionInput):
    title = serializers.CharField(max_length=200, required=False)
    starts_at = serializers.DateTimeField(required=False)
    ends_at = serializers.DateTimeField(required=False)


class SessionOutput(serializers.Serializer):
    public_id = serializers.UUIDField()
    title = serializers.CharField()
    description = serializers.CharField()
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField()
    location = serializers.UUIDField(allow_null=True)
    track = serializers.UUIDField(allow_null=True)
    speakers = serializers.CharField()
    stream_url = serializers.CharField()
    is_public = serializers.BooleanField()


def _data(session):
    return {
        "public_id": session.public_id,
        "title": session.title,
        "description": session.description,
        "starts_at": session.starts_at,
        "ends_at": session.ends_at,
        "location": session.location.public_id if session.location else None,
        "track": session.track.public_id if session.track else None,
        "speakers": session.speakers,
        "stream_url": session.stream_url,
        "is_public": session.is_public,
    }


class AgendaBase(OrganizerView):
    def apply(self, session, data, event):
        for name in ("title", "description", "starts_at", "ends_at", "speakers", "stream_url"):
            if name in data:
                setattr(session, name, data[name])
        if "is_public" in data:
            session.is_public = data["is_public"]
        if "location" in data:
            session.location = (
                get_object_or_404(Location, event=event, public_id=data["location"])
                if data["location"]
                else None
            )
        if "track" in data:
            session.track = (
                get_object_or_404(Track, event=event, public_id=data["track"])
                if data["track"]
                else None
            )
        try:
            session.full_clean()
        except ModelValidationError as exc:
            raise ValidationError(exc.message_dict) from exc
        session.save()


class AgendaListView(AgendaBase):
    @extend_schema(responses=SessionOutput(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        sessions = self.get_event().agenda_sessions.select_related("location", "track")
        return Response([_data(s) for s in sessions])

    @extend_schema(request=SessionInput, responses={201: SessionOutput})
    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        self.ensure_mutable(event)
        data = SessionInput(data=request.data)
        data.is_valid(raise_exception=True)
        with transaction.atomic():
            session = AgendaSession(event=event, created_by=request.user)
            self.apply(session, data.validated_data, event)
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="agenda.session_created",
                target=session,
            )
        return Response(_data(session), status=201)


class AgendaDetailView(AgendaBase):
    def get_session(self):
        return get_object_or_404(
            AgendaSession.objects.select_related("location", "track"),
            event=self.get_event(),
            public_id=self.kwargs["session_public_id"],
        )

    @extend_schema(responses=SessionOutput)
    def get(self, request, workspace_public_id, event_public_id, session_public_id):
        return Response(_data(self.get_session()))

    @extend_schema(request=SessionPatchInput, responses=SessionOutput)
    def patch(self, request, workspace_public_id, event_public_id, session_public_id):
        event = self.get_event()
        self.ensure_mutable(event)
        data = SessionPatchInput(data=request.data, partial=True)
        data.is_valid(raise_exception=True)
        with transaction.atomic():
            session = AgendaSession.objects.select_for_update(of=("self",)).get(
                pk=self.get_session().pk
            )
            self.apply(session, data.validated_data, event)
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="agenda.session_updated",
                target=session,
            )
        return Response(_data(session))

    @extend_schema(responses={204: None})
    def delete(self, request, workspace_public_id, event_public_id, session_public_id):
        event = self.get_event()
        self.ensure_mutable(event)
        with transaction.atomic():
            session = self.get_session()
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="agenda.session_deleted",
                target=session,
                metadata={"title": session.title},
            )
            session.delete()
        return Response(status=204)
