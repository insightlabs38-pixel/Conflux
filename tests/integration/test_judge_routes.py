import itertools
import random

import pytest
from accounts.models import User
from evaluations.models import (
    Assignment,
    AssignmentVersion,
    Ballot,
    ConflictOfInterest,
    EvaluationPlan,
)
from integrations.demo_scenarios import generate_demo_event
from onsite import routing
from onsite.models import Location, ProjectLocation
from test_sponsor_portal import client_for

pytestmark = pytest.mark.django_db


class Point:
    def __init__(self, pk, x, y):
        self.pk, self.x, self.y, self.parent_id = pk, x, y, None


def d(a, b):
    return routing.distance(a, b)


def test_exact_optimizer_matches_brute_force_and_respects_start():
    rng = random.Random(4)
    points = [Point(i + 1, rng.uniform(0, 50), rng.uniform(0, 50)) for i in range(7)]
    start = Point(99, 0, 0)
    best = min(routing.path_length(list(p), d, start) for p in itertools.permutations(points))
    route = routing.optimize(points, d, start)
    assert routing.path_length(route, d, start) == pytest.approx(best)
    open_best = min(routing.path_length(list(p), d) for p in itertools.permutations(points))
    assert routing.path_length(routing.optimize(points, d), d) == pytest.approx(open_best)
    assert routing.optimize(points, d, start) == routing.optimize(list(points), d, start)


def test_heuristic_for_large_routes_is_deterministic_and_never_worse_than_input_order():
    rng = random.Random(9)
    points = [Point(i + 1, rng.uniform(0, 100), rng.uniform(0, 100)) for i in range(14)]
    route = routing.optimize(points, d)
    assert sorted(p.pk for p in route) == sorted(p.pk for p in points)
    assert routing.path_length(route, d) <= routing.path_length(points, d)
    assert route == routing.optimize(points, d)


def test_distance_uses_coordinates_then_rooms_then_a_default():
    a, b = Point(1, 0, 0), Point(2, 3, 4)
    assert d(a, a) == 0 and d(a, b) == 5
    b.parent_id = 7
    assert d(a, b) == 5 + routing.ROOM_CHANGE
    c, e = Point(3, None, None), Point(4, None, None)
    c.parent_id = e.parent_id = 1
    assert d(c, e) == routing.SAME_ROOM
    e.parent_id = 2
    assert d(c, e) == routing.DIFFERENT_ROOM


def world():
    event = generate_demo_event(seed=41, participants=6, judges=3)
    prefix = "demo-hackathon-41-"
    users = {
        "org": User.objects.get(username=prefix + "organizer"),
        "part": User.objects.get(username=prefix + "participant-01"),
        **{f"j{i}": User.objects.get(username=f"{prefix}judge-0{i}") for i in (1, 2, 3)},
    }
    projects = list(event.projects.order_by("name"))
    hall = Location.objects.create(event=event, kind="room", name="Hall", x=0, y=0)
    xs = [50, 0, 40, 10, 30, 20]
    for index, project in enumerate(projects):
        table = Location.objects.create(
            event=event, kind="table", name=f"T{index}", parent=hall, x=xs[index], y=0
        )
        ProjectLocation.objects.create(project=project, location=table)
    plan = EvaluationPlan.objects.get(stage__event=event)
    return event, plan, users, projects


def urls(event, plan, suffix):
    return (
        f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}/stages/"
        f"{plan.stage.public_id}/evaluation-plans/{plan.public_id}/{suffix}"
    )


def test_judge_route_orders_only_remaining_expected_projects_and_shortens_the_walk():
    event, plan, users, projects = world()
    judge = client_for(users["j1"])
    first = judge.get(urls(event, plan, "my-route/"))
    assert first.status_code == 200, first.content
    assert first.json()["stops"] == []
    Ballot.objects.filter(judge=users["j1"]).delete()
    route = judge.get(urls(event, plan, "my-route/")).json()
    assert len(route["stops"]) == 6 and route["unplaced"] == []
    assert route["total_distance"] < route["baseline_distance"]
    positions = [int(s["location_name"][1:]) for s in route["stops"]]
    xs = [[50, 0, 40, 10, 30, 20][p] for p in positions]
    assert xs in ([0, 10, 20, 30, 40, 50], [50, 40, 30, 20, 10, 0])
    assert route["total_distance"] == 50.0
    started = judge.get(
        urls(event, plan, "my-route/") + f"?start={Location.objects.get(name='T0').public_id}"
    ).json()
    assert [s["location_name"] for s in started["stops"]][0] == "T0"


def test_conflicts_ineligible_and_unplaced_projects_never_appear_in_routes():
    from eligibility.models import EligibilityReview

    event, plan, users, projects = world()
    Ballot.objects.filter(judge=users["j1"]).delete()
    ConflictOfInterest.objects.create(
        event=event, judge=users["j1"], project=projects[0], declared_by=users["j1"]
    )
    EligibilityReview.objects.create(project=projects[1], status="ineligible")
    ProjectLocation.objects.filter(project=projects[2]).delete()
    route = client_for(users["j1"]).get(urls(event, plan, "my-route/")).json()
    names = {s["project_name"] for s in route["stops"]}
    assert names == {p.name for p in projects[3:]}
    assert route["unplaced"] == [str(projects[2].public_id)]


def test_assigned_subset_routes_follow_the_active_assignment_only():
    event, plan, users, projects = world()
    plan.pool_strategy = "assigned_subset"
    version = AssignmentVersion.objects.create(plan=plan, number=1, coverage=1)
    for project in projects[:3]:
        Assignment.objects.create(version=version, judge=users["j2"], project=project)
    EvaluationPlan.objects.filter(pk=plan.pk).update(
        pool_strategy="assigned_subset", active_assignment_version=version
    )
    Ballot.objects.filter(judge__in=[users["j1"], users["j2"]]).delete()
    two = client_for(users["j2"]).get(urls(event, plan, "my-route/")).json()
    assert {s["project_name"] for s in two["stops"]} == {p.name for p in projects[:3]}
    assert client_for(users["j1"]).get(urls(event, plan, "my-route/")).json()["stops"] == []


def test_organizer_overview_totals_and_access_control():
    event, plan, users, projects = world()
    Ballot.objects.all().delete()
    overview = client_for(users["org"]).get(urls(event, plan, "routes/")).json()
    assert [j["username"] for j in overview["judges"]] == [
        f"demo-hackathon-41-judge-0{i}" for i in (1, 2, 3)
    ]
    assert overview["total_distance"] == pytest.approx(
        sum(j["total_distance"] for j in overview["judges"])
    )
    assert overview["total_distance"] < overview["baseline_distance"]
    assert client_for(users["j1"]).get(urls(event, plan, "routes/")).status_code == 403
    assert client_for(users["part"]).get(urls(event, plan, "my-route/")).status_code == 403
    assert client_for(users["org"]).get(urls(event, plan, "my-route/")).status_code == 403
    assert (
        client_for(users["j1"])
        .get(urls(event, plan, "my-route/") + "?remaining_only=maybe")
        .status_code
        == 400
    )
    unknown = "00000000-0000-4000-8000-000000000000"
    assert (
        client_for(users["j1"])
        .get(urls(event, plan, "my-route/") + f"?start={unknown}")
        .status_code
        == 404
    )
    other_event = generate_demo_event(seed=42, participants=3, judges=2)
    foreign = Location.objects.create(event=other_event, kind="room", name="Elsewhere")
    assert (
        client_for(users["j1"])
        .get(urls(event, plan, "my-route/") + f"?start={foreign.public_id}")
        .status_code
        == 404
    )
