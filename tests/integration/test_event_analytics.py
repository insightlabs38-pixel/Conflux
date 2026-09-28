from datetime import timedelta

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from community.models import Vote, VotingPlan
from django.test import Client
from django.utils import timezone
from evaluations.models import (
    Assignment,
    AssignmentVersion,
    Ballot,
    ConflictOfInterest,
    EvaluationMode,
    EvaluationPlan,
    EvaluationPool,
    EvaluationPoolStrategy,
    PairwiseComparison,
    PoolMembership,
    RubricVersion,
)
from events.models import Event, EventApplication, EventStatus
from participation.models import Team, TeamMembership
from projects.models import Project, Submission, SubmissionVersion
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db
CRITERIA = [{"id": "c", "name": "Criterion", "weight": 1, "min_score": 0, "max_score": 10}]


@pytest.fixture
def case():
    actor = User.objects.create_user(username="analytics-organizer")
    workspace = Workspace.objects.create(name="Analytics", slug="analytics")
    Membership.objects.create(workspace=workspace, user=actor, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="Analytics", slug="analytics")
    client = Client()
    client.cookies["session"] = Session.issue(actor).token
    url = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/operations/analytics/"
    return dict(actor=actor, workspace=workspace, event=event, client=client, url=url)


def data(c, **query):
    response = c["client"].get(c["url"], query)
    assert response.status_code == 200, response.content
    return response.json()


def fixture(c):
    people = [User.objects.create_user(username=f"person-{i}") for i in range(4)]
    for person, status in zip(people, ["approved", "approved", "pending", "rejected"], strict=True):
        EventApplication.objects.create(event=c["event"], user=person, status=status)
        Membership.objects.create(workspace=c["workspace"], user=person, role=Role.PARTICIPANT)
    teams = [Team.objects.create(event=c["event"], name=f"Team {i}") for i in range(2)]
    TeamMembership.objects.create(team=teams[0], user=people[0])
    TeamMembership.objects.create(team=teams[0], user=people[2])
    stage = Stage.objects.create(event=c["event"], name="First")
    projects = [
        Project.objects.create(
            event=c["event"],
            name=f"Project {i}",
            created_by=c["actor"],
            team=teams[0] if i < 2 else None,
        )
        for i in range(3)
    ]
    submissions = [
        Submission.objects.create(project=project, stage=stage, updated_by=c["actor"])
        for project in projects
    ]
    receipt = SubmissionVersion.objects.create(
        submission=submissions[0], number=1, snapshot={}, digest="a" * 64, finalized_by=c["actor"]
    )
    submissions[0].status, submissions[0].current_version = "finalized", receipt
    submissions[0].save()
    receipt = SubmissionVersion.objects.create(
        submission=submissions[2], number=1, snapshot={}, digest="b" * 64, finalized_by=c["actor"]
    )
    submissions[2].current_version = receipt
    submissions[2].save()
    plan = VotingPlan.objects.create(
        event=c["event"], opens_at=timezone.now(), closes_at=timezone.now() + timedelta(days=1)
    )
    Vote.objects.create(plan=plan, project=projects[0], voter_key="private-voter-one")
    Vote.objects.create(plan=plan, project=projects[0], voter_key="private-voter-two")
    return people, stage, projects, submissions


def judging(c, stage, projects):
    judges = [User.objects.create_user(username=f"judge-{i}") for i in range(2)]
    pool = EvaluationPool.objects.create(event=c["event"], name="Pool")
    for judge in judges:
        Membership.objects.create(workspace=c["workspace"], user=judge, role=Role.JUDGE)
        PoolMembership.objects.create(pool=pool, judge=judge)
    plan = EvaluationPlan.objects.create(
        stage=stage, name="Plan", pool=pool, pool_strategy=EvaluationPoolStrategy.ASSIGNED_SUBSET
    )
    old = RubricVersion.objects.create(plan=plan, number=1, criteria=CRITERIA)
    current = RubricVersion.objects.create(plan=plan, number=2, criteria=CRITERIA)
    Ballot.objects.create(rubric_version=old, judge=judges[0], project=projects[0])
    Ballot.objects.create(rubric_version=old, judge=judges[0], project=projects[1])
    Ballot.objects.create(rubric_version=current, judge=judges[0], project=projects[0])
    Ballot.objects.create(rubric_version=current, judge=judges[0], project=projects[1])
    Ballot.objects.create(
        rubric_version=current, judge=judges[1], project=projects[0], is_calibration=True
    )
    previous = AssignmentVersion.objects.create(plan=plan, number=1, coverage=1, evidence={})
    active = AssignmentVersion.objects.create(plan=plan, number=2, coverage=1, evidence={})
    Assignment.objects.create(version=previous, judge=judges[0], project=projects[1])
    Assignment.objects.create(version=active, judge=judges[0], project=projects[0])
    plan.active_assignment_version = active
    plan.save()
    return plan, judges


def test_empty_event_returns_unknown_ratios_and_no_writes(case):
    result = data(case)
    assert result["event"] == str(case["event"].public_id)
    assert result["registration"]["applications"] == 0
    assert result["registration"]["approval"] == {"numerator": 0, "denominator": 0, "ratio": None}
    assert result["teams"]["total"] == 0
    assert result["submissions"]["finalized_projects"]["ratio"] is None
    assert result["judging"]["plans"] == []
    assert result["voting"]["configured"] is False
    assert not AuditEvent.objects.exists()


def test_funnel_uses_explicit_event_local_denominators_and_current_submission_state(case):
    people, stage, projects, submissions = fixture(case)
    unrelated = User.objects.create_user(username="workspace-only")
    Membership.objects.create(workspace=case["workspace"], user=unrelated, role=Role.PARTICIPANT)
    result = data(case)
    assert result["registration"]["applications"] == 4
    assert result["registration"]["by_status"] == {
        "approved": 2,
        "pending": 1,
        "rejected": 1,
        "waitlisted": 0,
    }
    assert result["registration"]["approval"]["ratio"] == 0.5
    assert result["registration"]["approved_teamed"] == {
        "numerator": 1,
        "denominator": 2,
        "ratio": 0.5,
    }
    assert result["teams"]["project_creation"] == {"numerator": 1, "denominator": 2, "ratio": 0.5}
    assert result["teams"]["with_members"] == 1
    assert result["submissions"]["with_submission"]["ratio"] == 1
    assert result["submissions"]["finalized_projects"]["numerator"] == 1
    assert result["submissions"]["finalized_records"] == 1
    assert result["submissions"]["draft_records"] == 2
    assert result["submissions"]["immutable_versions"] == 2
    assert result["voting"]["votes"] == 2
    assert result["voting"]["project_engagement"]["numerator"] == 1
    assert "private-voter" not in str(result)
    assert not AuditEvent.objects.exists()


def test_multistage_finalization_counts_each_project_once(case):
    _, stage, projects, submissions = fixture(case)
    later = Stage.objects.create(event=case["event"], name="Later")
    submission = Submission.objects.create(
        project=projects[0], stage=later, updated_by=case["actor"]
    )
    receipt = SubmissionVersion.objects.create(
        submission=submission, number=1, snapshot={}, digest="c" * 64, finalized_by=case["actor"]
    )
    submission.status, submission.current_version = "finalized", receipt
    submission.save()
    result = data(case)["submissions"]
    assert result["finalized_records"] == 2
    assert result["finalized_projects"]["numerator"] == 1


def test_judging_excludes_historical_rubrics_assignments_and_calibration(case):
    _, stage, projects, _ = fixture(case)
    plan, judges = judging(case, stage, projects)
    row = data(case)["judging"]["plans"][0]
    assert row["completion"] == {"numerator": 1, "denominator": 1, "ratio": 1}
    assert row["current_judges"] == 1
    assert row["candidates"] == 3


def test_current_conflicts_and_pool_membership_change_completion_denominator(case):
    _, stage, projects, _ = fixture(case)
    plan, judges = judging(case, stage, projects)
    ConflictOfInterest.objects.create(
        event=case["event"], judge=judges[0], project=projects[0], declared_by=case["actor"]
    )
    row = data(case)["judging"]["plans"][0]
    assert row["completion"] == {"numerator": 0, "denominator": 0, "ratio": None}
    assert row["conflicting_pairs"] == 1


def test_all_judges_completion_excludes_conflicts_and_calibration(case):
    _, stage, projects, _ = fixture(case)
    plan, judges = judging(case, stage, projects)
    plan.pool_strategy = EvaluationPoolStrategy.ALL_JUDGES
    plan.save()
    ConflictOfInterest.objects.create(
        event=case["event"], judge=judges[1], project=projects[2], declared_by=case["actor"]
    )
    row = data(case)["judging"]["plans"][0]
    assert row["completion"] == {"numerator": 2, "denominator": 5, "ratio": 0.4}
    assert row["current_judges"] == 1


def test_pairwise_metrics_do_not_invent_a_rubric_completion_rate(case):
    _, stage, projects, _ = fixture(case)
    plan, judges = judging(case, stage, projects)
    plan.mode = EvaluationMode.PAIRWISE
    plan.save()
    PairwiseComparison.objects.create(
        plan=plan, judge=judges[0], project_a=projects[0], project_b=projects[1], winner=projects[0]
    )
    row = data(case)["judging"]["plans"][0]
    assert row["completion"] is None
    assert row["pairwise_comparisons"] == 1
    assert row["current_judges"] == 1


def test_foreign_event_activity_never_enters_the_funnel(case):
    people, stage, projects, _ = fixture(case)
    other = Event.objects.create(workspace=case["workspace"], name="Other", slug="other")
    EventApplication.objects.create(event=other, user=people[0], status="approved")
    team = Team.objects.create(event=other, name="Other")
    TeamMembership.objects.create(team=team, user=people[1])
    Project.objects.create(event=other, team=team, name="Other", created_by=case["actor"])
    result = data(case)
    assert result["registration"]["applications"] == 4
    assert result["registration"]["approved_teamed"]["numerator"] == 1
    assert result["teams"]["total"] == 2
    assert result["submissions"]["projects"] == 3


def test_unknown_judging_denominators_remain_unknown(case):
    _, stage, projects, _ = fixture(case)
    plan, judges = judging(case, stage, projects)
    plan.active_assignment_version = None
    plan.save()
    assert data(case)["judging"]["plans"][0]["completion"] is None


def test_removed_pool_judges_do_not_count_as_current_completions(case):
    _, stage, projects, _ = fixture(case)
    plan, judges = judging(case, stage, projects)
    PoolMembership.objects.filter(pool=plan.pool, judge=judges[0]).delete()
    row = data(case)["judging"]["plans"][0]
    assert row["pool_judges"] == 1
    assert row["completion"] == {"numerator": 0, "denominator": 0, "ratio": None}
    assert row["current_judges"] == 0


def test_finalized_flag_without_a_receipt_is_not_completed_submission_evidence(case):
    _, stage, projects, submissions = fixture(case)
    Submission.objects.filter(pk=submissions[1].pk).update(status="finalized")
    result = data(case)["submissions"]
    assert result["finalized_records"] == result["finalized_projects"]["numerator"] == 1


def test_permissions_archive_readability_and_input_validation(case):
    assert Client().get(case["url"]).status_code in (401, 403)
    outsider = User.objects.create_user(username="outside")
    client = Client()
    client.cookies["session"] = Session.issue(outsider).token
    assert client.get(case["url"]).status_code == 403
    Membership.objects.create(workspace=case["workspace"], user=outsider, role=Role.PARTICIPANT)
    assert client.get(case["url"]).status_code == 403
    Event.objects.filter(pk=case["event"].pk).update(status=EventStatus.ARCHIVED)
    assert data(case)["event"] == str(case["event"].public_id)
    assert case["client"].get(case["url"], {"plan_offset": -1}).status_code == 400
    assert case["client"].get(case["url"], {"plan_offset": "bad"}).status_code == 400
    assert (
        case["client"].post(case["url"], data={}, content_type="application/json").status_code
        == 405
    )


def test_judging_pages_are_bounded_and_nonoverlapping(case):
    stage = Stage.objects.create(event=case["event"], name="Stage")
    EvaluationPlan.objects.bulk_create(
        [EvaluationPlan(stage=stage, name=f"Plan {n}") for n in range(51)]
    )
    first = data(case)["judging"]
    second = data(case, plan_offset=50)["judging"]
    assert first["plan_count"] == second["plan_count"] == 51
    assert len(first["plans"]) == 50
    assert first["next_offset"] == 50
    assert len(second["plans"]) == 1
    assert second["next_offset"] is None
    assert not {plan["public_id"] for plan in first["plans"]} & {
        plan["public_id"] for plan in second["plans"]
    }
