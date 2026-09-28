"""PVS10: mentor availability, a bounded help-request queue and
office-hours scheduling. Participants see request status and office-hours
capacity; the mentor/organizer-only surfaces (queue, attendee lists) stay
separate so a participant's own read access never leaks other projects'
requests.
"""

from accounts.authentication import CookieSessionAuthentication
from accounts.models import User
from core.authz import has_any_role
from core.permissions import IsWorkspaceMember
from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from events.models import Event, Track
from projects.models import Project
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role, Workspace

from .models import MentorProfile, MentorRequest, OfficeHourSignup, OfficeHourSlot, RequestStatus
from .services import (
    cancel_office_hours_signup,
    cancel_request,
    claim_request,
    create_request,
    reassign_request,
    resolve_request,
    sign_up_for_office_hours,
)


class MentorshipEventView(APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    def get_workspace(self):
        if not hasattr(self, "_workspace"):
            self._workspace = get_object_or_404(
                Workspace, public_id=self.kwargs["workspace_public_id"]
            )
        return self._workspace

    def get_event(self):
        return get_object_or_404(
            Event, workspace=self.get_workspace(), public_id=self.kwargs["event_public_id"]
        )

    def is_mentor_like(self, request):
        return has_any_role(
            request.user, self.get_workspace(), Role.MENTOR, Role.ORGANIZER, Role.ADMIN
        )

    def is_organizer(self, request):
        return has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN)


def _profile_data(profile):
    return {
        "public_id": str(profile.public_id),
        "mentor": profile.mentor.username,
        "headline": profile.headline,
        "is_available": profile.is_available,
        "track_expertise": [str(t.public_id) for t in profile.track_expertise.all()],
    }


def _request_data(item, *, include_project=True):
    data = {
        "public_id": str(item.public_id),
        "topic": item.topic,
        "urgency": item.urgency,
        "status": item.status,
        "track": str(item.track.public_id) if item.track_id else None,
        "claimed_by": item.claimed_by.username if item.claimed_by_id else None,
        "resolution_note": item.resolution_note,
        "created_at": item.created_at,
        "claimed_at": item.claimed_at,
        "resolved_at": item.resolved_at,
    }
    if include_project:
        data["project"] = str(item.project.public_id)
        data["project_name"] = item.project.name
    return data


def _slot_data(slot, request, *, is_manager):
    data = {
        "public_id": str(slot.public_id),
        "mentor": slot.mentor.username,
        "track": str(slot.track.public_id) if slot.track_id else None,
        "starts_at": slot.starts_at,
        "ends_at": slot.ends_at,
        "location": slot.location,
        "capacity": slot.capacity,
        "signup_count": slot.signups.count(),
    }
    if is_manager:
        data["attendees"] = [
            {"public_id": str(item.public_id), "project": item.project.name}
            for item in slot.signups.select_related("project")
        ]
    else:
        mine = slot.signups.filter(project__memberships__user=request.user).first()
        data["my_signup"] = str(mine.public_id) if mine else None
    return data


class MentorProfileListView(MentorshipEventView):
    @extend_schema(responses=None)
    def get(self, request, workspace_public_id, event_public_id):
        profiles = MentorProfile.objects.filter(
            event=self.get_event(), is_available=True
        ).select_related("mentor")
        return Response([_profile_data(item) for item in profiles.order_by("mentor__username")])


class MentorProfileSelfView(MentorshipEventView):
    @extend_schema(request=None, responses=None)
    def put(self, request, workspace_public_id, event_public_id):
        if not self.is_mentor_like(request):
            raise ValidationError("Only a mentor or organizer can hold a mentor profile.")
        event = self.get_event()
        profile, _ = MentorProfile.objects.get_or_create(event=event, mentor=request.user)
        profile.headline = str(request.data.get("headline", profile.headline))[:200]
        profile.is_available = bool(request.data.get("is_available", profile.is_available))
        track_ids = request.data.get("track_expertise")
        if track_ids is not None:
            tracks = Track.objects.filter(event=event, public_id__in=track_ids)
            if tracks.count() != len(set(track_ids)):
                raise ValidationError({"track_expertise": "Every track must belong to this event."})
            profile.track_expertise.set(tracks)
        try:
            profile.full_clean()
            profile.save()
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(_profile_data(profile))


class ProjectMentorRequestView(MentorshipEventView):
    def get_project(self):
        return get_object_or_404(
            Project,
            event=self.get_event(),
            public_id=self.kwargs["project_public_id"],
            memberships__user=self.request.user,
        )

    @extend_schema(responses=None)
    def get(self, request, workspace_public_id, event_public_id, project_public_id):
        requests = MentorRequest.objects.filter(project=self.get_project()).select_related(
            "claimed_by", "track"
        )
        return Response([_request_data(item, include_project=False) for item in requests])

    @extend_schema(request=None, responses={201: None})
    def post(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.get_project()
        track = None
        if request.data.get("track"):
            track = get_object_or_404(Track, event=project.event, public_id=request.data["track"])
        try:
            item = create_request(
                project,
                request.user,
                track=track,
                topic=str(request.data.get("topic", "")).strip(),
                urgency=request.data.get("urgency", "normal"),
            )
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(_request_data(item, include_project=False), status=201)


class MentorRequestQueueView(MentorshipEventView):
    @extend_schema(responses=None)
    def get(self, request, workspace_public_id, event_public_id):
        if not self.is_mentor_like(request):
            raise ValidationError("Only a mentor or organizer can see the queue.")
        requests = MentorRequest.objects.filter(
            event=self.get_event(), status__in=(RequestStatus.PENDING, RequestStatus.CLAIMED)
        ).select_related("project", "claimed_by", "track")
        return Response([_request_data(item) for item in requests])


class MentorRequestBase(MentorshipEventView):
    def get_request(self, request_public_id):
        return get_object_or_404(MentorRequest, event=self.get_event(), public_id=request_public_id)


class MentorRequestClaimView(MentorRequestBase):
    @extend_schema(request=None, responses=None)
    def post(self, request, workspace_public_id, event_public_id, request_public_id):
        try:
            item = claim_request(self.get_request(request_public_id), request.user)
        except ModelValidationError as exc:
            raise ValidationError(exc.messages if hasattr(exc, "messages") else str(exc)) from exc
        return Response(_request_data(item))


class MentorRequestReassignView(MentorRequestBase):
    @extend_schema(request=None, responses=None)
    def post(self, request, workspace_public_id, event_public_id, request_public_id):
        to_mentor = get_object_or_404(User, public_id=request.data.get("to_mentor"))
        try:
            item = reassign_request(
                self.get_request(request_public_id), request.user, to_mentor=to_mentor
            )
        except ModelValidationError as exc:
            raise ValidationError(exc.messages if hasattr(exc, "messages") else str(exc)) from exc
        return Response(_request_data(item))


class MentorRequestResolveView(MentorRequestBase):
    @extend_schema(request=None, responses=None)
    def post(self, request, workspace_public_id, event_public_id, request_public_id):
        try:
            item = resolve_request(
                self.get_request(request_public_id),
                request.user,
                note=str(request.data.get("note", "")),
            )
        except ModelValidationError as exc:
            raise ValidationError(exc.messages if hasattr(exc, "messages") else str(exc)) from exc
        return Response(_request_data(item))


class MentorRequestCancelView(MentorRequestBase):
    @extend_schema(request=None, responses=None)
    def post(self, request, workspace_public_id, event_public_id, request_public_id):
        try:
            item = cancel_request(self.get_request(request_public_id), request.user)
        except ModelValidationError as exc:
            raise ValidationError(exc.messages if hasattr(exc, "messages") else str(exc)) from exc
        return Response(_request_data(item))


class OfficeHourSlotListView(MentorshipEventView):
    @extend_schema(responses=None)
    def get(self, request, workspace_public_id, event_public_id):
        is_manager = self.is_mentor_like(request)
        slots = OfficeHourSlot.objects.filter(
            event=self.get_event(), ends_at__gte=timezone.now()
        ).select_related("mentor", "track")
        return Response([_slot_data(item, request, is_manager=is_manager) for item in slots])

    @extend_schema(request=None, responses={201: None})
    def post(self, request, workspace_public_id, event_public_id):
        if not self.is_mentor_like(request):
            raise ValidationError("Only a mentor or organizer can schedule office hours.")
        event = self.get_event()
        track = None
        if request.data.get("track"):
            track = get_object_or_404(Track, event=event, public_id=request.data["track"])
        slot = OfficeHourSlot(
            event=event,
            mentor=request.user,
            track=track,
            starts_at=request.data.get("starts_at"),
            ends_at=request.data.get("ends_at"),
            location=str(request.data.get("location", ""))[:200],
            capacity=request.data.get("capacity", 1),
        )
        try:
            slot.full_clean()
            slot.save()
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(_slot_data(slot, request, is_manager=True), status=201)


class OfficeHourSignupListView(MentorshipEventView):
    @extend_schema(request=None, responses={201: None})
    def post(self, request, workspace_public_id, event_public_id, slot_public_id):
        slot = get_object_or_404(OfficeHourSlot, event=self.get_event(), public_id=slot_public_id)
        project = get_object_or_404(
            Project, event=self.get_event(), public_id=request.data.get("project")
        )
        try:
            signup = sign_up_for_office_hours(slot, project, request.user)
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response({"public_id": str(signup.public_id)}, status=201)


class OfficeHourSignupDetailView(MentorshipEventView):
    @extend_schema(responses={204: None})
    def delete(self, request, workspace_public_id, event_public_id, signup_public_id):
        signup = get_object_or_404(
            OfficeHourSignup, slot__event=self.get_event(), public_id=signup_public_id
        )
        try:
            cancel_office_hours_signup(signup, request.user)
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(status=204)
