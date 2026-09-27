import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.assignment import compute_assignment
from evaluations.connectivity import connectivity_report
from evaluations.models import (
    ConflictOfInterest,
    EvaluationPlan,
    EvaluationPool,
    EvaluationPoolStrategy,
    PoolMembership,
)
from events.models import Event, Track
from projects.models import Project, Submission
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

CRITERIA = [{"id": "impact", "name": "Impact", "weight": 1, "min_score": 0, "max_score": 10}]


def cookie_client(token):
    client = Client()
    client.cookies["session"] = token
    return client


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


def urls(workspace, event, stage=None, plan=None):
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
    if stage and plan:
        return f"{base}/stages/{stage.public_id}/evaluation-plans/{plan.public_id}"
    return base


def test_assignment_detail_returns_a_parseable_null_before_any_activation():
    workspace, event, stage, pool, plan, organizer, judges, projects = make_fixture(judge_count=1)
    organizer_client = cookie_client(Session.issue(organizer).token)
    response = organizer_client.get(urls(workspace, event, stage, plan) + "/assignments/")
    assert response.status_code == 200
    assert response.json() is None


def test_all_judges_strategy_pairs_every_judge_with_every_candidate_minus_conflicts():
    _, event, stage, pool, plan, organizer, judges, projects = make_fixture()
    plan.pool_strategy = EvaluationPoolStrategy.ALL_JUDGES
    plan.save()
    ConflictOfInterest.objects.create(
        event=event, judge=judges[0], project=projects[0], declared_by=organizer
    )
    pairs = {(p.judge_id, p.project_id) for p in compute_assignment(plan)}
    expected = {(j.id, p.id) for j in judges for p in projects} - {(judges[0].id, projects[0].id)}
    assert pairs == expected


def test_assigned_subset_is_deterministic_and_respects_conflicts_and_coverage():
    _, event, stage, pool, plan, organizer, judges, projects = make_fixture(
        judge_count=3, project_count=2
    )
    ConflictOfInterest.objects.create(
        event=event, judge=judges[0], project=projects[0], declared_by=organizer
    )
    first = compute_assignment(plan, coverage=2)
    second = compute_assignment(plan, coverage=2)
    assert first == second
    for pairing in first:
        if pairing.project_id == projects[0].id:
            assert pairing.judge_id != judges[0].id
    counts = {}
    for pairing in first:
        counts[pairing.project_id] = counts.get(pairing.project_id, 0) + 1
    assert all(count <= 2 for count in counts.values())


def test_activation_endpoint_freezes_a_version_and_enforces_it_on_ballots():
    workspace, event, stage, pool, plan, organizer, judges, projects = make_fixture(
        judge_count=2, project_count=2
    )
    organizer_client = cookie_client(Session.issue(organizer).token)
    plan.save()  # ensure draft_criteria persisted before publish
    base = urls(workspace, event, stage, plan)
    organizer_client.post(base + "/publish-rubric/")

    activated = organizer_client.post(
        base + "/assignments/activate/", data={"coverage": 1}, content_type="application/json"
    )
    assert activated.status_code == 201
    assert activated.json()["coverage"] == 1
    assert activated.json()["evidence"]["connectivity"]["connected"] is True

    plan.refresh_from_db()
    assigned_judge_id = (
        plan.active_assignment_version.assignments.filter(project=projects[0]).first().judge_id
    )
    assigned_judge = next(j for j in judges if j.id == assigned_judge_id)
    unassigned_judge = next(j for j in judges if j.id != assigned_judge_id)

    assigned_client = cookie_client(Session.issue(assigned_judge).token)
    ok = assigned_client.post(
        base + "/ballots/",
        data={
            "project": str(projects[0].public_id),
            "responses": [{"criterion_id": "impact", "score": 5}],
        },
        content_type="application/json",
    )
    assert ok.status_code == 201

    unassigned_client = cookie_client(Session.issue(unassigned_judge).token)
    blocked = unassigned_client.post(
        base + "/ballots/",
        data={
            "project": str(projects[0].public_id),
            "responses": [{"criterion_id": "impact", "score": 5}],
        },
        content_type="application/json",
    )
    assert blocked.status_code == 400


def test_ballot_rejected_outright_for_a_declared_conflict_even_under_all_judges():
    workspace, event, stage, pool, plan, organizer, judges, projects = make_fixture(
        judge_count=1, project_count=1
    )
    plan.pool_strategy = EvaluationPoolStrategy.ALL_JUDGES
    plan.save()
    ConflictOfInterest.objects.create(
        event=event, judge=judges[0], project=projects[0], declared_by=judges[0]
    )
    organizer_client = cookie_client(Session.issue(organizer).token)
    base = urls(workspace, event, stage, plan)
    organizer_client.post(base + "/publish-rubric/")

    judge_client = cookie_client(Session.issue(judges[0]).token)
    response = judge_client.post(
        base + "/ballots/",
        data={
            "project": str(projects[0].public_id),
            "responses": [{"criterion_id": "impact", "score": 1}],
        },
        content_type="application/json",
    )
    assert response.status_code == 400


def test_judges_can_self_declare_conflicts_and_only_organizers_see_all():
    workspace, event, stage, pool, plan, organizer, judges, projects = make_fixture(
        judge_count=2, project_count=1
    )
    judge_a_client = cookie_client(Session.issue(judges[0]).token)
    conflicts_url = urls(workspace, event) + "/judge-conflicts/"
    created = judge_a_client.post(
        conflicts_url,
        data={"project": str(projects[0].public_id), "reason": "I mentored this team"},
        content_type="application/json",
    )
    assert created.status_code == 201

    judge_b_client = cookie_client(Session.issue(judges[1]).token)
    assert judge_b_client.get(conflicts_url).json() == []

    organizer_client = cookie_client(Session.issue(organizer).token)
    assert len(organizer_client.get(conflicts_url).json()) == 1


def test_pool_membership_requires_the_judge_role():
    workspace, event, stage, pool, plan, organizer, judges, projects = make_fixture(judge_count=1)
    participant = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(user=participant, workspace=workspace, role=Role.PARTICIPANT)
    organizer_client = cookie_client(Session.issue(organizer).token)
    response = organizer_client.post(
        urls(workspace, event) + f"/evaluation-pools/{pool.public_id}/memberships/",
        data={"judge": str(participant.public_id)},
        content_type="application/json",
    )
    assert response.status_code == 400


def test_track_fit_now_discriminates_using_the_real_project_track_association():
    # Corrective fix ahead of C-B15: Project previously had no Track at all,
    # so this factor always tied at 0 regardless of expertise. Two judges,
    # one candidate on Track "AI" -- only the AI-expert judge should fit.
    workspace, event, stage, pool, plan, organizer, judges, projects = make_fixture(
        judge_count=2, project_count=1
    )
    ai_track = Track.objects.create(event=event, name="AI")
    projects[0].track = ai_track
    projects[0].save()
    expert, non_expert = judges
    PoolMembership.objects.filter(pool=pool, judge=expert).first().track_expertise.set([ai_track])

    pairs = compute_assignment(plan, coverage=1)
    assert [p.judge_id for p in pairs] == [expert.id]


def test_track_fit_is_a_harmless_no_op_for_a_project_with_no_track():
    workspace, event, stage, pool, plan, organizer, judges, projects = make_fixture(
        judge_count=2, project_count=1
    )
    ai_track = Track.objects.create(event=event, name="AI")
    PoolMembership.objects.filter(pool=pool, judge=judges[0]).first().track_expertise.set(
        [ai_track]
    )
    assert projects[0].track is None

    pairs = compute_assignment(plan, coverage=1)
    # No track on the candidate -> falls back to load/id tie-break, not fit.
    assert [p.judge_id for p in pairs] == [judges[0].id]


def test_coverage_one_is_repaired_into_a_connected_graph_when_possible():
    # Pathological (JDG-012): coverage=1 never creates a shared candidate on
    # its own, so without the connectivity repair every judge would be its
    # own isolated component.
    _, event, stage, pool, plan, organizer, judges, projects = make_fixture(
        judge_count=4, project_count=4
    )
    pairs = compute_assignment(plan, coverage=1)
    judge_ids = {p.judge_id for p in pairs}
    report = connectivity_report(pairs, judge_ids)
    assert report.connected


def test_assignment_infeasible_to_fully_connect_still_reports_honestly():
    # Two judges, two candidates, and a conflict on every possible bridge:
    # repair cannot succeed, and the report must say so rather than lie.
    _, event, stage, pool, plan, organizer, judges, projects = make_fixture(
        judge_count=2, project_count=2
    )
    ConflictOfInterest.objects.create(
        event=event, judge=judges[0], project=projects[1], declared_by=organizer
    )
    ConflictOfInterest.objects.create(
        event=event, judge=judges[1], project=projects[0], declared_by=organizer
    )
    pairs = compute_assignment(plan, coverage=1)
    judge_ids = {p.judge_id for p in pairs}
    report = connectivity_report(pairs, judge_ids)
    assert not report.connected
