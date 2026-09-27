import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.assignment import activate, rebalance
from evaluations.connectivity import connectivity_report
from evaluations.models import (
    Assignment,
    Ballot,
    BallotResponse,
    EvaluationPlan,
    EvaluationPool,
    EvaluationPoolStrategy,
    PoolMembership,
    RubricVersion,
)
from events.models import Event
from projects.models import Project, Submission
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

CRITERIA = [{"id": "impact", "name": "Impact", "weight": 1, "min_score": 0, "max_score": 10}]


def cookie_client(token):
    client = Client()
    client.cookies["session"] = token
    return client


def make_fixture(judge_count=4, project_count=3, label="a"):
    organizer = User.objects.create_user(username=f"organizer_{label}", password="unused")
    workspace = Workspace.objects.create(name=f"Dogfood {label}", slug=f"dogfood-{label}")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    stage = Stage.objects.create(event=event, name="Finals")
    pool = EvaluationPool.objects.create(event=event, name="Main pool")
    judges = []
    for i in range(judge_count):
        judge = User.objects.create_user(username=f"judge{i}_{label}", password="unused")
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
    return workspace, event, stage, plan, organizer, judges, projects


def url(workspace, event, stage, plan, suffix=""):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/{plan.public_id}/{suffix}"
    )


def submit_ballot(plan, judge, project):
    version = RubricVersion.objects.filter(plan=plan).order_by("-number").first()
    ballot = Ballot.objects.create(rubric_version=version, judge=judge, project=project)
    BallotResponse.objects.create(ballot=ballot, criterion_id="impact", score=5)
    return ballot


def test_rebalance_keeps_submitted_pairings_and_reassigns_pending_ones():
    _, event, stage, plan, organizer, judges, projects = make_fixture(
        judge_count=4, project_count=3
    )
    RubricVersion.objects.create(plan=plan, number=1, criteria=CRITERIA)
    activate(plan, coverage=2)

    dropped = judges[0]
    # The dropped judge already submitted a real ballot for projects[0]: it
    # must survive rebalancing even though the judge is being dropped.
    submit_ballot(plan, dropped, projects[0])

    version = rebalance(plan, drop_judge_ids={dropped.id})
    pairs = {(a.judge_id, a.project_id) for a in version.assignments.all()}

    # The submitted pairing survives.
    assert (dropped.id, projects[0].id) in pairs
    # No *pending* pairing for the dropped judge remains.
    submitted_pairs = {(dropped.id, projects[0].id)}
    assert all(
        judge_id != dropped.id or (judge_id, project_id) in submitted_pairs
        for judge_id, project_id in pairs
    )
    # Every project is still at (at least) the original coverage.
    counts = {}
    for judge_id, project_id in pairs:
        counts[project_id] = counts.get(project_id, 0) + 1
    assert all(count >= 2 for count in counts.values())


def _as_relative_pairs(pairs, judges, projects):
    judge_index = {j.id: i for i, j in enumerate(judges)}
    project_index = {p.id: i for i, p in enumerate(projects)}
    return {(judge_index[j], project_index[p]) for j, p in pairs}


def test_rebalance_is_deterministic_and_preserves_connectivity():
    _, event, stage, plan, organizer, judges, projects = make_fixture(
        judge_count=4, project_count=3, label="a"
    )
    RubricVersion.objects.create(plan=plan, number=1, criteria=CRITERIA)
    activate(plan, coverage=2)
    first = rebalance(plan, drop_judge_ids={judges[0].id})
    first_pairs = {(a.judge_id, a.project_id) for a in first.assignments.all()}
    first_relative = _as_relative_pairs(first_pairs, judges, projects)

    # An identically-shaped second plan (same relative structure, different
    # absolute ids) must rebalance to the same relative result.
    _, event2, stage2, plan2, _, judges2, projects2 = make_fixture(
        judge_count=4, project_count=3, label="b"
    )
    RubricVersion.objects.create(plan=plan2, number=1, criteria=CRITERIA)
    activate(plan2, coverage=2)
    second = rebalance(plan2, drop_judge_ids={judges2[0].id})
    second_pairs = {(a.judge_id, a.project_id) for a in second.assignments.all()}
    second_relative = _as_relative_pairs(second_pairs, judges2, projects2)
    assert first_relative == second_relative

    active_ids = [j.id for j in judges[1:]]
    report = connectivity_report(
        [Assignment(judge_id=j, project_id=p) for j, p in first_pairs], active_ids
    )
    assert report.connected


def test_rebalance_raises_without_an_active_assignment():
    _, event, stage, plan, organizer, judges, projects = make_fixture()
    with pytest.raises(ValueError):
        rebalance(plan, drop_judge_ids={judges[0].id})


def test_rebalance_raises_for_all_judges_strategy():
    _, event, stage, plan, organizer, judges, projects = make_fixture()
    plan.pool_strategy = EvaluationPoolStrategy.ALL_JUDGES
    plan.save(update_fields=["pool_strategy"])
    with pytest.raises(ValueError):
        rebalance(plan, drop_judge_ids={judges[0].id})


def test_rebalance_endpoint_creates_a_new_version_and_records_an_audit_event():
    workspace, event, stage, plan, organizer, judges, projects = make_fixture(
        judge_count=4, project_count=3
    )
    organizer_client = cookie_client(Session.issue(organizer).token)
    organizer_client.post(url(workspace, event, stage, plan, "publish-rubric/"))
    organizer_client.post(
        url(workspace, event, stage, plan, "assignments/activate/"),
        data={"coverage": 2},
        content_type="application/json",
    )

    response = organizer_client.post(
        url(workspace, event, stage, plan, "assignments/rebalance/"),
        data={"drop_judges": [str(judges[0].public_id)]},
        content_type="application/json",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["number"] == 2
    assert body["evidence"]["dropped_judges"] == [judges[0].id]
    assert body["evidence"]["rebalanced_from"] == 1


def test_rebalance_endpoint_is_organizer_only():
    workspace, event, stage, plan, organizer, judges, projects = make_fixture()
    client = cookie_client(Session.issue(judges[1]).token)
    response = client.post(
        url(workspace, event, stage, plan, "assignments/rebalance/"),
        data={"drop_judges": [str(judges[0].public_id)]},
        content_type="application/json",
    )
    assert response.status_code == 403
