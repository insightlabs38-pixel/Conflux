"""Public, unauthenticated event-logistics surfaces (agenda page, iCalendar feed,
expo map, state JSON and status badge). All go through get_public_event, so an
unpublished event or unreleased archive is a 404 exactly as for the gallery."""

from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.html import escape
from drf_spectacular.utils import extend_schema
from presentation.models import Page
from presentation.public import get_public_event, public_projects
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import agenda
from .models import Location, LocationKind


def public_sessions(event):
    return event.agenda_sessions.filter(is_public=True).select_related("location", "track")


def _theme(event):
    page = Page.objects.filter(event=event).first()
    return page.theme if page else "default"


def agenda_page(request, event_public_id):
    event = get_public_event(event_public_id)
    sessions = list(public_sessions(event))
    for session in sessions:
        session.embed = agenda.embed_url(session.stream_url)
    return render(
        request,
        "onsite/agenda.html",
        {"event": event, "theme": _theme(event), "sessions": sessions},
    )


def agenda_ics(request, event_public_id):
    event = get_public_event(event_public_id)
    body = agenda.build_ics(event, public_sessions(event), request.get_host())
    response = HttpResponse(body, content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = 'inline; filename="agenda.ics"'
    return response


def expo_map(request, event_public_id):
    event = get_public_event(event_public_id)
    public = {p.pk: p for p in public_projects(event)}
    places = []
    for location in Location.objects.filter(event=event).select_related("parent"):
        if location.kind == LocationKind.ROOM:
            continue
        projects = [
            a.project for a in location.projects.select_related("project") if a.project_id in public
        ]
        places.append({"location": location, "projects": projects})
    rooms = list(Location.objects.filter(event=event, kind=LocationKind.ROOM))
    return render(
        request,
        "onsite/map.html",
        {"event": event, "theme": _theme(event), "places": places, "rooms": rooms},
    )


def _event_state(event_public_id):
    event = get_public_event(event_public_id)
    now = timezone.now()
    sessions = public_sessions(event)
    live = [s.title for s in sessions.filter(starts_at__lte=now, ends_at__gt=now)]
    upcoming = sessions.filter(starts_at__gt=now).first()
    return {
        "name": event.name,
        "status": event.status,
        "phase": agenda.event_phase(event, now),
        "starts_at": event.starts_at,
        "ends_at": event.ends_at,
        "now": now,
        "live_sessions": live,
        "next_session": {"title": upcoming.title, "starts_at": upcoming.starts_at}
        if upcoming
        else None,
        "projects": public_projects(event).count(),
    }


_COLORS = {"live": "#146c43", "upcoming": "#8a5a00", "ended": "#56626d"}


def badge(request, event_public_id):
    event = get_public_event(event_public_id)
    phase = agenda.event_phase(event)
    left, right = escape(event.name[:24]), escape(phase.upper())
    width_left, width_right = 12 + 7 * len(event.name[:24]), 12 + 8 * len(phase)
    total = width_left + width_right
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="22" role="img" '
        f'aria-label="{left}: {right}"><rect width="{width_left}" height="22" fill="#16202b"/>'
        f'<rect x="{width_left}" width="{width_right}" height="22" fill="{_COLORS[phase]}"/>'
        '<g fill="#fff" font-family="system-ui,sans-serif" font-size="12">'
        f'<text x="6" y="15">{left}</text>'
        f'<text x="{width_left + 6}" y="15">{right}</text></g></svg>'
    )
    response = HttpResponse(svg, content_type="image/svg+xml")
    return response


def _agenda_items(event_public_id):
    event = get_public_event(event_public_id)
    return [
        {
            "title": session.title,
            "description": session.description,
            "starts_at": session.starts_at,
            "ends_at": session.ends_at,
            "location": session.location.name if session.location else None,
            "track": session.track.name if session.track else None,
            "speakers": session.speakers,
            "stream_url": session.stream_url,
            "embed_url": agenda.embed_url(session.stream_url),
        }
        for session in public_sessions(event)
    ]


class PublicSessionOutput(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField()
    location = serializers.CharField(allow_null=True)
    track = serializers.CharField(allow_null=True)
    speakers = serializers.CharField()
    stream_url = serializers.CharField()
    embed_url = serializers.CharField(allow_null=True)


class NextSession(serializers.Serializer):
    title = serializers.CharField()
    starts_at = serializers.DateTimeField()


class EventStateOutput(serializers.Serializer):
    name = serializers.CharField()
    status = serializers.CharField()
    phase = serializers.ChoiceField(choices=["upcoming", "live", "ended"])
    starts_at = serializers.DateTimeField(allow_null=True)
    ends_at = serializers.DateTimeField(allow_null=True)
    now = serializers.DateTimeField()
    live_sessions = serializers.ListField(child=serializers.CharField())
    next_session = NextSession(allow_null=True)
    projects = serializers.IntegerField()


class PublicAgendaView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=PublicSessionOutput(many=True))
    def get(self, request, event_public_id):
        return Response(_agenda_items(event_public_id))


class EventStateView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=EventStateOutput)
    def get(self, request, event_public_id):
        response = Response(_event_state(event_public_id))
        response["Access-Control-Allow-Origin"] = "*"
        return response
