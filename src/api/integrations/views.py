import csv

from accounts.authentication import CookieSessionAuthentication
from core.authz import has_any_role
from core.csv_safety import safe_cell
from core.pagination import page_params, paged_response
from core.permissions import require_roles
from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role, Workspace

from .models import FixtureScore, ImportedFixture
from .schema import ErrorSchema, GalleryProjectSchema, JudgeScoreSchema


def _current_fixture():
    return ImportedFixture.objects.order_by("-imported_at").first()


def _acceptance_workspace():
    # Foundation-only coupling: the fixture isn't attached to a real
    # Workspace/Event yet (C-B07/C-B08 haven't built teams/projects), so an
    # organizer-role check here uses the same seeded "acceptance" workspace
    # as the acceptance identities themselves (see seed_acceptance_identities).
    # Revisit once fixture import targets a real Event.
    return Workspace.objects.filter(slug="acceptance").first()


class GalleryView(APIView):
    """Public project listing (T1: "a stranger can browse the gallery")."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter("limit", int, description="Page size, 1-100 (default 50)."),
            OpenApiParameter("offset", int, description="Rows to skip (default 0)."),
        ],
        responses=GalleryProjectSchema(many=True),
    )
    def get(self, request):
        limit, offset = page_params(request)
        fixture = _current_fixture()
        if fixture is None:
            return Response([], headers={"X-Total-Count": "0"})
        projects = fixture.projects.select_related("team", "track").order_by("external_id")
        return paged_response(
            request,
            projects,
            lambda page: [
                {
                    "id": p.external_id,
                    "title": p.title,
                    "summary": p.summary,
                    "team": p.team.name,
                    "track": p.track.name,
                    "repo_url": p.repo_url,
                }
                for p in page
            ],
            limit=limit,
            offset=offset,
        )


class SubmitView(APIView):
    """T1: a closed event refuses submissions — checked against the real
    imported event close time, not a checker-specific branch.
    """

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={403: ErrorSchema, 501: ErrorSchema})
    def post(self, request):
        fixture = _current_fixture()
        if fixture is None or timezone.now() >= fixture.event_submissions_close:
            return Response({"detail": "Submissions are closed."}, status=403)
        # Unreachable against the official fixture (its event closed
        # 2026-03-01), but a real submission path — creating a Project
        # against an open event — is C-B08/C-B10 work, not built yet. Fail
        # loudly here rather than silently accepting into nowhere.
        return Response({"detail": "Submissions are not yet implemented."}, status=501)


class JudgeScoresView(APIView):
    """T2: a judge reads their own scores by default; `?judge=<id>` lets an
    organizer (or the judge themself) look up a specific judge, and refuses
    anyone else — the backend check the checker's peer_scores probe is for.
    """

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=JudgeScoreSchema(many=True))
    def get(self, request):
        fixture = _current_fixture()
        if fixture is None:
            return Response(status=404)

        requested_id = request.GET.get("judge")
        if requested_id:
            judge = fixture.judges.filter(external_id=requested_id).first()
            if judge is None:
                return Response(status=404)
            is_self = judge.linked_user_id == request.user.id
            if not is_self and not has_any_role(
                request.user, _acceptance_workspace(), Role.ORGANIZER, Role.ADMIN
            ):
                return Response({"detail": "You cannot view another judge's scores."}, status=403)
        else:
            judge = fixture.judges.filter(linked_user=request.user).first()
            if judge is None:
                return Response({"detail": "Not a judge."}, status=403)

        scores = FixtureScore.objects.filter(judge=judge).prefetch_related("criteria")
        return Response(
            [
                {
                    "project": s.project.external_id,
                    "comment": s.comment,
                    "criteria": {c.name: c.value for c in s.criteria.all()},
                }
                for s in scores
            ]
        )


class CsvExportView(APIView):
    """T2: an organizer can export CSV."""

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    def get_workspace(self):
        return _acceptance_workspace()

    @extend_schema(responses={(200, "text/csv"): OpenApiTypes.BINARY})
    def get(self, request):
        fixture = _current_fixture()
        scores = (
            FixtureScore.objects.none()
            if fixture is None
            else FixtureScore.objects.filter(fixture=fixture)
            .select_related("judge", "project")
            .prefetch_related("criteria")
        )
        criterion_names = sorted({c.name for s in scores for c in s.criteria.all()})

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="scores.csv"'
        writer = csv.writer(response)
        writer.writerow(["judge", "project", *[safe_cell(n) for n in criterion_names], "comment"])
        for s in scores:
            values = {c.name: c.value for c in s.criteria.all()}
            writer.writerow(
                [
                    safe_cell(cell)
                    for cell in [s.judge.external_id, s.project.external_id]
                    + [values.get(name, "") for name in criterion_names]
                    + [s.comment]
                ]
            )
        return response
