import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.assignment import Pairing
from evaluations.models import (
    ConflictOfInterest,
    EvaluationPlan,
    EvaluationPool,
    EvaluationPoolStrategy,
    PoolMembership,
)
from evaluations.optimization import (
    MinCostFlow,
    compare,
    compute_assignment_optimized,
)
from events.models import Event, Track
from projects.models import Project, Submission
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

CRITERIA = [{"id": "impact", "name": "Impact", "weight": 1, "min_score": 0, "max_score": 10}]


def make_fixture(judge_count=2, project_count=2):
    organizer = User.objects.create_user(username="organizer", password="unused")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    stage = Stage.objects.create(event=event, name="Finals")
    pool = EvaluationPool.objects.create(event=event, name="Main pool")
    judges = []
    for i in range(judge_count):
        judge = User.objects.create_user(username=f"judge{i}", password="unused")
        Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
        PoolMembership.objects.create(pool=pool, judge=judge)
        judges.append(judge)
    projects = []
    for i in range(project_count):
        project = Project.objects.create(event=event, name=f"Project {i}", created_by=organizer)
        Submission.objects.create(project=project, stage=stage, updated_by=organizer)
        projects.append(project)
    plan = EvaluationPlan.objects.create(
        stage=stage,
        name="Judge panel",
        pool=pool,
        pool_strategy=EvaluationPoolStrategy.ASSIGNED_SUBSET,
        draft_criteria=CRITERIA,
    )
    return workspace, event, stage, pool, plan, organizer, judges, projects


def cookie_client(token):
    client = Client()
    client.cookies["session"] = token
    return client


def urls(workspace, event, stage, plan):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/{plan.public_id}"
    )


def test_min_cost_flow_finds_the_optimal_track_fit_matching():
    # A fits P (cost 0), B fits Q (cost 0); a cross pairing costs 1 each.
    solver = MinCostFlow(6)
    for judge in (1, 2):
        solver.add_edge(0, judge, 1, 0)
        solver.add_edge(0, judge, 1, 1)
    solver.add_edge(1, 3, 1, 0)
    solver.add_edge(1, 4, 1, 1)
    solver.add_edge(2, 3, 1, 1)
    solver.add_edge(2, 4, 1, 0)
    solver.add_edge(3, 5, 1, 0)
    solver.add_edge(4, 5, 1, 0)
    flow, cost = solver.solve(0, 5, 2)
    assert (flow, cost) == (2, 0)


def test_min_cost_flow_balances_load_via_convex_cost():
    # 2 judges, 4 equally-cheap projects, coverage 1 -> optimal split is
    # 2/2, not 4/0, since marginal cost rises 0,1,2,3 for each judge.
    sink = 7
    solver = MinCostFlow(sink + 1)
    for judge in (1, 2):
        for marginal in range(4):
            solver.add_edge(0, judge, 1, marginal)
    for project in range(3, 7):
        solver.add_edge(1, project, 1, 0)
        solver.add_edge(2, project, 1, 0)
        solver.add_edge(project, sink, 1, 0)
    flow, cost = solver.solve(0, sink, 4)
    assert flow == 4
    load = {
        judge: sum(1 for edge in solver.graph[judge] if edge.to in range(3, 7) and edge.cap == 0)
        for judge in (1, 2)
    }
    assert set(load.values()) == {2}


def test_optimized_assignment_never_produces_a_conflicted_pair_and_respects_coverage():
    _, event, stage, pool, plan, organizer, judges, projects = make_fixture(
        judge_count=3, project_count=2
    )
    ConflictOfInterest.objects.create(
        event=event, judge=judges[0], project=projects[0], declared_by=organizer
    )
    pairs = compute_assignment_optimized(plan, coverage=2)
    assert (judges[0].id, projects[0].id) not in {(p.judge_id, p.project_id) for p in pairs}
    counts = {}
    for pairing in pairs:
        counts[pairing.project_id] = counts.get(pairing.project_id, 0) + 1
    assert all(count <= 2 for count in counts.values())


def test_optimized_assignment_prefers_track_fit_when_load_allows():
    _, event, stage, pool, plan, organizer, judges, projects = make_fixture(
        judge_count=2, project_count=1
    )
    ai_track = Track.objects.create(event=event, name="AI")
    projects[0].track = ai_track
    projects[0].save()
    PoolMembership.objects.filter(pool=pool, judge=judges[0]).first().track_expertise.set(
        [ai_track]
    )
    pairs = compute_assignment_optimized(plan, coverage=1)
    assert pairs == [Pairing(judges[0].id, projects[0].id)]


def test_optimized_assignment_is_deterministic():
    _, event, stage, pool, plan, organizer, judges, projects = make_fixture(
        judge_count=3, project_count=4
    )
    first = compute_assignment_optimized(plan, coverage=2)
    second = compute_assignment_optimized(plan, coverage=2)
    assert {(p.judge_id, p.project_id) for p in first} == {
        (p.judge_id, p.project_id) for p in second
    }


def test_optimized_assignment_balances_load_better_than_a_naive_single_judge_dump():
    _, event, stage, pool, plan, organizer, judges, projects = make_fixture(
        judge_count=2, project_count=6
    )
    pairs = compute_assignment_optimized(plan, coverage=1)
    load = {}
    for pairing in pairs:
        load[pairing.judge_id] = load.get(pairing.judge_id, 0) + 1
    # Not a hard 3/3 split: repair_connectivity (shared with the heuristic)
    # may add one bridging assignment where coverage=1 leaves no overlap
    # between judges to begin with. The convex load cost still keeps the
    # split tight rather than dumping everything on one judge.
    assert max(load.values()) - min(load.values()) <= 1


def test_optimization_only_applies_to_assigned_subset():
    _, event, stage, pool, plan, organizer, judges, projects = make_fixture()
    plan.pool_strategy = EvaluationPoolStrategy.ALL_JUDGES
    plan.save()
    with pytest.raises(ValueError, match="assigned-subset"):
        compute_assignment_optimized(plan)


def test_compare_reports_both_solvers_and_their_connectivity():
    _, event, stage, pool, plan, organizer, judges, projects = make_fixture(
        judge_count=3, project_count=3
    )
    result = compare(plan, coverage=1)
    assert result["heuristic"]["solver"] == "heuristic"
    assert result["optimized"]["solver"] == "optimized"
    assert result["heuristic"]["coverage"] == result["optimized"]["coverage"] == 1
    assert "connectivity" in result["heuristic"] and "connectivity" in result["optimized"]


def test_activate_optimized_freezes_a_version_and_enforces_it_on_ballots():
    workspace, event, stage, pool, plan, organizer, judges, projects = make_fixture(
        judge_count=2, project_count=2
    )
    organizer_client = cookie_client(Session.issue(organizer).token)
    base = urls(workspace, event, stage, plan)
    organizer_client.post(base + "/publish-rubric/")

    activated = organizer_client.post(
        base + "/assignments/activate-optimized/",
        data={"coverage": 1},
        content_type="application/json",
    )
    assert activated.status_code == 201
    assert activated.json()["evidence"]["solver"] == "optimized"

    plan.refresh_from_db()
    assigned_judge_id = (
        plan.active_assignment_version.assignments.filter(project=projects[0]).first().judge_id
    )
    assigned_judge = next(j for j in judges if j.id == assigned_judge_id)
    unassigned_judge = next(j for j in judges if j.id != assigned_judge_id)

    ok = cookie_client(Session.issue(assigned_judge).token).post(
        base + "/ballots/",
        data={
            "project": str(projects[0].public_id),
            "responses": [{"criterion_id": "impact", "score": 5}],
        },
        content_type="application/json",
    )
    assert ok.status_code == 201
    blocked = cookie_client(Session.issue(unassigned_judge).token).post(
        base + "/ballots/",
        data={
            "project": str(projects[0].public_id),
            "responses": [{"criterion_id": "impact", "score": 5}],
        },
        content_type="application/json",
    )
    assert blocked.status_code == 400


def test_compare_and_activate_optimized_reject_the_all_judges_strategy():
    workspace, event, stage, pool, plan, organizer, judges, projects = make_fixture()
    plan.pool_strategy = EvaluationPoolStrategy.ALL_JUDGES
    plan.save()
    organizer_client = cookie_client(Session.issue(organizer).token)
    base = urls(workspace, event, stage, plan)
    organizer_client.post(base + "/publish-rubric/")

    compare_response = organizer_client.post(
        base + "/assignments/compare/", data={"coverage": 1}, content_type="application/json"
    )
    assert compare_response.status_code == 400
    activate_response = organizer_client.post(
        base + "/assignments/activate-optimized/",
        data={"coverage": 1},
        content_type="application/json",
    )
    assert activate_response.status_code == 400


def test_participant_cannot_reach_compare_or_activate_optimized():
    workspace, event, stage, pool, plan, organizer, judges, projects = make_fixture()
    participant = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(user=participant, workspace=workspace, role=Role.PARTICIPANT)
    client = cookie_client(Session.issue(participant).token)
    base = urls(workspace, event, stage, plan)

    assert (
        client.post(
            base + "/assignments/compare/", data={"coverage": 1}, content_type="application/json"
        ).status_code
        == 403
    )
    assert (
        client.post(
            base + "/assignments/activate-optimized/",
            data={"coverage": 1},
            content_type="application/json",
        ).status_code
        == 403
    )
