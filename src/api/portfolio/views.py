"""PVS14: a read-only, workspace-wide view of people and projects across events.

Nothing is stored here. Participants see only their own memberships; organizers see
the whole workspace. Awards appear only once the award is published, and only the
fields already public for that award."""

from accounts.authentication import CookieSessionAuthentication
from accounts.models import User
from awards.models import AwardWinner
from core.permissions import IsWorkspaceMember, require_roles
from django.db.models import Count, Max, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from projects.models import Project, ProjectMembership, SubmissionStatus
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role, Workspace

DEFAULT_LIMIT = 50
MAX_LIMIT = 100


def _page(request):
    def number(name, default, high):
        raw = request.query_params.get(name, default)
        try:
            value = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValidationError({name: "Must be an integer."}) from exc
        if not 0 <= value <= high:
            raise ValidationError({name: f"Must be between 0 and {high}."})
        return value

    limit = number("limit", DEFAULT_LIMIT, MAX_LIMIT)
    return max(limit, 1), number("offset", 0, 10**7)


def _q(request):
    value = request.query_params.get("q", "").strip()
    if len(value) > 100:
        raise ValidationError({"q": "At most 100 characters."})
    return value


class WorkspaceView(APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    def get_workspace(self):
        if not hasattr(self, "_workspace"):
            self._workspace = get_object_or_404(
                Workspace, public_id=self.kwargs["workspace_public_id"]
            )
        return self._workspace


class OrganizerWorkspaceView(WorkspaceView):
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]


def project_rows(projects):
    """Serialize projects with fixed-cost extra queries (no per-row lookups)."""
    projects = list(
        projects.select_related("event", "team", "track").prefetch_related(
            "submissions__stage", "submissions__current_version"
        )
    )
    wins = {}
    for win in AwardWinner.objects.filter(
        project__in=projects, award__published_at__isnull=False
    ).select_related("award"):
        wins.setdefault(win.project_id, []).append(
            {"award": win.award.name, "award_id": str(win.award.public_id)}
        )
    rows = []
    for project in projects:
        event = project.event
        submissions = [
            {
                "stage": s.stage.name,
                "stage_id": str(s.stage.public_id),
                "status": s.status,
                "finalized_at": s.current_version.finalized_at
                if s.status == SubmissionStatus.FINALIZED and s.current_version
                else None,
                "version": s.current_version.number
                if s.status == SubmissionStatus.FINALIZED and s.current_version
                else None,
            }
            for s in sorted(project.submissions.all(), key=lambda s: s.stage.position)
        ]
        rows.append(
            {
                "project": str(project.public_id),
                "name": project.name,
                "event": {
                    "public_id": str(event.public_id),
                    "name": event.name,
                    "status": event.status,
                    "starts_at": event.starts_at,
                    "ends_at": event.ends_at,
                },
                "team": project.team.name if project.team else None,
                "track": project.track.name if project.track else None,
                "submissions": submissions,
                "finalized": any(s["status"] == SubmissionStatus.FINALIZED for s in submissions),
                "awards": wins.get(project.pk, []),
            }
        )
    return rows


def _ordered(projects):
    return projects.order_by("-event__starts_at", "event__name", "name", "id")


def _member_projects(workspace, user):
    return Project.objects.filter(event__workspace=workspace, memberships__user=user).distinct()


class MyPortfolioView(WorkspaceView):
    @extend_schema(responses={200: {"type": "object"}})
    def get(self, request, workspace_public_id):
        rows = project_rows(_ordered(_member_projects(self.get_workspace(), request.user)))
        return Response(
            {
                "events": len({row["event"]["public_id"] for row in rows}),
                "projects": rows,
            }
        )


class PortfolioProjectListView(OrganizerWorkspaceView):
    @extend_schema(
        parameters=[
            OpenApiParameter("event", str),
            OpenApiParameter("status", str, enum=["finalized", "unfinalized"]),
            OpenApiParameter("q", str),
            OpenApiParameter("limit", int),
            OpenApiParameter("offset", int),
        ],
        responses={200: {"type": "object"}},
    )
    def get(self, request, workspace_public_id):
        projects = Project.objects.filter(event__workspace=self.get_workspace())
        event = request.query_params.get("event")
        if event:
            projects = projects.filter(event__public_id=_uuid(event, "event"))
        status = request.query_params.get("status")
        finalized = Q(submissions__status=SubmissionStatus.FINALIZED)
        if status == "finalized":
            projects = projects.filter(finalized)
        elif status == "unfinalized":
            projects = projects.exclude(pk__in=Project.objects.filter(finalized).values("pk"))
        elif status:
            raise ValidationError({"status": "Must be 'finalized' or 'unfinalized'."})
        q = _q(request)
        if q:
            projects = projects.filter(name__icontains=q)
        projects = _ordered(projects.distinct())
        limit, offset = _page(request)
        total = projects.count()
        return Response(
            {
                "total": total,
                "limit": limit,
                "offset": offset,
                "results": project_rows(projects[offset : offset + limit]),
            }
        )


def _uuid(value, name):
    import uuid

    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise ValidationError({name: "Must be a UUID."}) from exc


class PortfolioParticipantListView(OrganizerWorkspaceView):
    @extend_schema(
        parameters=[
            OpenApiParameter("q", str),
            OpenApiParameter("limit", int),
            OpenApiParameter("offset", int),
        ],
        responses={200: {"type": "object"}},
    )
    def get(self, request, workspace_public_id):
        memberships = ProjectMembership.objects.filter(
            project__event__workspace=self.get_workspace()
        )
        q = _q(request)
        if q:
            memberships = memberships.filter(user__username__icontains=q)
        grouped = (
            memberships.values("user_id", "user__username", "user__public_id")
            .annotate(
                events=Count("project__event_id", distinct=True),
                projects=Count("project_id", distinct=True),
                finalized=Count(
                    "project_id",
                    filter=Q(project__submissions__status=SubmissionStatus.FINALIZED),
                    distinct=True,
                ),
                last_joined_at=Max("joined_at"),
            )
            .order_by("-last_joined_at", "user__username", "user_id")
        )
        limit, offset = _page(request)
        total = grouped.count()
        return Response(
            {
                "total": total,
                "limit": limit,
                "offset": offset,
                "results": [
                    {
                        "user": str(row["user__public_id"]),
                        "username": row["user__username"],
                        "events": row["events"],
                        "projects": row["projects"],
                        "finalized_projects": row["finalized"],
                        "last_joined_at": row["last_joined_at"],
                    }
                    for row in grouped[offset : offset + limit]
                ],
            }
        )


class PortfolioParticipantDetailView(OrganizerWorkspaceView):
    @extend_schema(responses={200: {"type": "object"}})
    def get(self, request, workspace_public_id, user_public_id):
        workspace = self.get_workspace()
        user = get_object_or_404(User, public_id=user_public_id)
        projects = _member_projects(workspace, user)
        if not projects.exists():
            return Response({"detail": "Not found."}, status=404)
        rows = project_rows(_ordered(projects))
        return Response(
            {
                "user": str(user.public_id),
                "username": user.username,
                "events": len({row["event"]["public_id"] for row in rows}),
                "projects": rows,
            }
        )
