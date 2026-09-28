from accounts.authentication import CookieSessionAuthentication
from core.authz import has_any_role
from core.permissions import IsWorkspaceMember, require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from events.models import PUBLICLY_VISIBLE_STATUSES, Event
from projects.models import Project
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role, Workspace

from . import services
from .models import SEEKING_CHOICES, ProjectContinuation

PUBLIC_UPDATES = 3


class ContinuationInput(serializers.Serializer):
    summary = serializers.CharField(max_length=1000)
    url = serializers.URLField(required=False, allow_blank=True)
    seeking = serializers.ListField(
        child=serializers.ChoiceField(choices=SEEKING_CHOICES), required=False
    )
    is_public = serializers.BooleanField(required=False)


class UpdateInput(serializers.Serializer):
    body = serializers.CharField(max_length=1000)


class ModerationInput(serializers.Serializer):
    reason = serializers.CharField(max_length=300, required=False, allow_blank=True)


def guarded(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ModelValidationError as exc:
            raise ValidationError(exc.messages) from exc

    wrapper.__name__ = fn.__name__
    return wrapper


def _iso(value):
    return value.isoformat() if value else None


def _data(item, *, updates=None, private=False):
    updates = list(item.updates.all()) if updates is None else updates
    data = {
        "project": str(item.project.public_id),
        "name": item.project.name,
        "summary": item.summary,
        "url": item.url,
        "seeking": item.seeking,
        "updated_at": _iso(item.updated_at),
        "updates": [{"body": u.body, "posted_at": _iso(u.created_at)} for u in updates],
    }
    if private:
        data.update(
            is_public=item.is_public,
            hidden=item.hidden_at is not None,
            hidden_reason=item.hidden_reason,
            public_id=str(item.public_id),
        )
    return data


class ContinuationView(APIView):
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

    def is_organizer(self, request):
        return has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN)

    def member_project(self, request):
        project = get_object_or_404(
            Project.objects.select_related("event"),
            event=self.get_event(),
            public_id=self.kwargs["project_public_id"],
        )
        if not (
            self.is_organizer(request) or project.memberships.filter(user=request.user).exists()
        ):
            raise Http404
        return project


class ProjectContinuationView(ContinuationView):
    @extend_schema(responses={200: {"type": "object"}})
    def get(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.member_project(request)
        item = ProjectContinuation.objects.filter(project=project).first()
        if item is None:
            raise Http404
        return Response(_data(item, private=True))

    @extend_schema(request=ContinuationInput, responses={200: {"type": "object"}})
    @guarded
    def put(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.member_project(request)
        data = request.data
        item = services.save_continuation(
            project,
            request.user,
            summary=data.get("summary"),
            url=data.get("url", ""),
            seeking=data.get("seeking", []),
            is_public=data.get("is_public", False),
        )
        return Response(_data(item, private=True))


class ContinuationUpdateView(ContinuationView):
    @extend_schema(request=UpdateInput, responses={201: {"type": "object"}})
    @guarded
    def post(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.member_project(request)
        update = services.add_update(project, request.user, body=request.data.get("body"))
        return Response({"body": update.body, "posted_at": _iso(update.created_at)}, status=201)


class ContinuationModerationView(ContinuationView):
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]
    hide = True

    @extend_schema(request=ModerationInput, responses={200: {"type": "object"}})
    @guarded
    def post(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.member_project(request)
        item = get_object_or_404(ProjectContinuation, project=project)
        item = services.set_hidden(
            item, request.user, hidden=self.hide, reason=str(request.data.get("reason", ""))
        )
        return Response(_data(item, private=True))


class OrganizerContinuationListView(ContinuationView):
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(responses={200: {"type": "array", "items": {"type": "object"}}})
    def get(self, request, workspace_public_id, event_public_id):
        items = (
            ProjectContinuation.objects.filter(project__event=self.get_event())
            .select_related("project")
            .prefetch_related("updates")
        )
        return Response([_data(i, private=True) for i in items])


class PublicContinuationListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses={200: {"type": "array", "items": {"type": "object"}}})
    def get(self, request, event_public_id):
        event = get_object_or_404(
            Event, public_id=event_public_id, is_public=True, status__in=PUBLICLY_VISIBLE_STATUSES
        )
        items = (
            ProjectContinuation.objects.filter(
                project__event=event, is_public=True, hidden_at__isnull=True
            )
            .select_related("project")
            .prefetch_related("updates")
            .order_by("-updated_at", "id")
        )
        return Response([_data(i, updates=list(i.updates.all())[:PUBLIC_UPDATES]) for i in items])
