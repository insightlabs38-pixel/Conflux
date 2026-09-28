from dataclasses import dataclass

from accounts.authentication import CookieSessionAuthentication
from accounts.models import User
from core.permissions import require_roles
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from evaluations.candidates import judge_candidates
from evaluations.models import Ballot, EvaluationPlan, PairwiseComparison, PoolMembership
from events.models import Event
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

from . import routing
from .models import Location, LocationKind, ProjectLocation

PARAMETERS = [
    OpenApiParameter("start", str, description="Location id to start walking from."),
    OpenApiParameter("remaining_only", bool, description="Skip projects already evaluated."),
]


@dataclass(frozen=True)
class Stop:
    project: object
    location: object


def _walk(a, b):
    return routing.distance(a.location, b.location)


class RouteBase(APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    def get_workspace(self):
        if not hasattr(self, "_workspace"):
            self._workspace = get_object_or_404(
                Workspace, public_id=self.kwargs["workspace_public_id"]
            )
        return self._workspace

    def get_plan(self):
        workspace = self.get_workspace()
        event = get_object_or_404(
            Event, workspace=workspace, public_id=self.kwargs["event_public_id"]
        )
        stage = get_object_or_404(Stage, event=event, public_id=self.kwargs["stage_public_id"])
        return (
            workspace,
            event,
            get_object_or_404(EvaluationPlan, stage=stage, public_id=self.kwargs["plan_public_id"]),
        )

    def options(self, request, event):
        raw = request.query_params.get("remaining_only", "true").lower()
        if raw not in ("true", "false"):
            raise ValidationError({"remaining_only": "Use true or false."})
        start = None
        if request.query_params.get("start"):
            start = get_object_or_404(
                Location, event=event, public_id=request.query_params["start"]
            )
        return raw == "true", start

    def route_for(self, plan, judge, remaining_only, start):
        candidates = list(judge_candidates(plan, judge).order_by("name", "pk"))
        done = set()
        if remaining_only:
            done = set(
                Ballot.objects.filter(
                    rubric_version__plan=plan, judge=judge, is_calibration=False
                ).values_list("project_id", flat=True)
            )
            for a, b in PairwiseComparison.objects.filter(plan=plan, judge=judge).values_list(
                "project_a_id", "project_b_id"
            ):
                done |= {a, b}
        todo = [p for p in candidates if p.pk not in done]
        placed = {
            row.project_id: row.location
            for row in ProjectLocation.objects.filter(
                project__in=todo, location__kind__in=[LocationKind.TABLE, LocationKind.BOOTH]
            ).select_related("location")
        }
        stops = [Stop(p, placed[p.pk]) for p in todo if p.pk in placed]
        origin = Stop(None, start) if start is not None else None
        ordered = routing.optimize(stops, _walk, origin)
        length = routing.path_length(ordered, _walk, origin)
        baseline = routing.path_length(stops, _walk, origin)
        legs, previous = [], origin
        for stop in ordered:
            location = stop.location
            legs.append(
                {
                    "project": str(stop.project.public_id),
                    "project_name": stop.project.name,
                    "location": str(location.public_id),
                    "location_name": location.name,
                    "room": location.parent.name if location.parent_id else None,
                    "leg_distance": round(_walk(previous, stop) if previous else 0.0, 2),
                }
            )
            previous = stop
        return {
            "stops": legs,
            "total_distance": round(length, 2),
            "baseline_distance": round(baseline, 2),
            "unplaced": [str(p.public_id) for p in todo if p.pk not in placed],
            "already_evaluated": len(done & {p.pk for p in candidates}),
        }


class MyRouteView(RouteBase):
    permission_classes = [require_roles(Role.JUDGE)]

    @extend_schema(parameters=PARAMETERS, responses=OpenApiTypes.OBJECT)
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        workspace, event, plan = self.get_plan()
        remaining_only, start = self.options(request, event)
        return Response(self.route_for(plan, request.user, remaining_only, start))


class RoutesView(RouteBase):
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(parameters=PARAMETERS, responses=OpenApiTypes.OBJECT)
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        workspace, event, plan = self.get_plan()
        remaining_only, start = self.options(request, event)
        if plan.pool_id:
            judge_ids = PoolMembership.objects.filter(pool_id=plan.pool_id).values_list(
                "judge_id", flat=True
            )
        else:
            judge_ids = Membership.objects.filter(workspace=workspace, role=Role.JUDGE).values_list(
                "user_id", flat=True
            )
        rows = []
        for judge in User.objects.filter(id__in=judge_ids).order_by("username"):
            route = self.route_for(plan, judge, remaining_only, start)
            rows.append({"judge": str(judge.public_id), "username": judge.username, **route})
        return Response(
            {
                "judges": rows,
                "total_distance": round(sum(r["total_distance"] for r in rows), 2),
                "baseline_distance": round(sum(r["baseline_distance"] for r in rows), 2),
            }
        )
