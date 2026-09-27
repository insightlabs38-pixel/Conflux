import pytest
from accounts.models import Session, User
from awards.models import Award, SelectionSource
from django.test import Client
from evaluations.models import EvaluationPlan, EvaluationPool, PoolMembership
from events.models import Event
from policies.models import TemporalGate
from projects.models import Project, Submission, SubmissionStatus
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

CRITERIA = [{"id": "impact", "name": "Impact", "weight": 1, "min_score": 0, "max_score": 10}]


def cookie_client(token):
    client = Client()
    client.cookies["session"] = token
    return client


def make_fixture():
    organizer = User.objects.create_user(username="organizer", password="unused")
    judge_a = User.objects.create_user(username="judge_a", password="unused")
    judge_b = User.objects.create_user(username="judge_b", password="unused")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge_a, workspace=workspace, role=Role.JUDGE)
    Membership.objects.create(user=judge_b, workspace=workspace, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    stage = Stage.objects.create(event=event, name="Finals")
    project = Project.objects.create(event=event, name="Autograder", created_by=organizer)
    Submission.objects.create(
        project=project, stage=stage, updated_by=organizer, status=SubmissionStatus.FINALIZED
    )
    return workspace, event, stage, project, organizer, judge_a, judge_b


def plans_url(workspace, event, stage, suffix=""):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/{suffix}"
    )


def calendar_url(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/judge-calendar/"


def workload_url(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/judge-workload/"


def make_all_judges_plan(organizer_client, workspace, event, stage):
    plan_id = organizer_client.post(
        plans_url(workspace, event, stage),
        data={"name": "Panel", "draft_criteria": CRITERIA},
        content_type="application/json",
    ).json()["public_id"]
    organizer_client.post(plans_url(workspace, event, stage, f"{plan_id}/publish-rubric/"))
    return plan_id


def submit_ballot(client, workspace, event, stage, plan_id, project):
    return client.post(
        plans_url(workspace, event, stage, f"{plan_id}/ballots/"),
        data={
            "project": str(project.public_id),
            "responses": [{"criterion_id": "impact", "score": 8}],
        },
        content_type="application/json",
    )


def test_judge_calendar_lists_windows_and_updates_after_a_ballot():
    workspace, event, stage, project, organizer, judge_a, _ = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    TemporalGate.objects.create(event=event, name="Judging window")
    plan_id = make_all_judges_plan(organizer_client, workspace, event, stage)

    judge_client = cookie_client(Session.issue(judge_a).token)
    before = judge_client.get(calendar_url(workspace, event)).json()
    assert before["windows"] == [
        {
            "name": "Judging window",
            "opens_at": None,
            "closes_at": None,
            "status": "open",
        }
    ]
    assert before["assignments"] == [
        {
            "stage_name": "Finals",
            "plan": plan_id,
            "plan_name": "Panel",
            "rubric_published": True,
            "assigned_count": 1,
            "submitted_count": 0,
            "completion_ratio": 0.0,
        }
    ]

    submit_ballot(judge_client, workspace, event, stage, plan_id, project)
    after = judge_client.get(calendar_url(workspace, event)).json()
    assert after["assignments"][0]["submitted_count"] == 1
    assert after["assignments"][0]["completion_ratio"] == 1.0


def test_judge_calendar_excludes_a_judge_not_in_the_prize_pool():
    workspace, event, stage, project, organizer, judge_a, judge_b = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    pool = EvaluationPool.objects.create(event=event, name="Sponsor pool")
    PoolMembership.objects.create(pool=pool, judge=judge_a)
    plan_id = organizer_client.post(
        plans_url(workspace, event, stage),
        data={
            "name": "Prize",
            "draft_criteria": CRITERIA,
            "prize_judging": True,
            "pool": str(pool.public_id),
        },
        content_type="application/json",
    ).json()["public_id"]
    organizer_client.post(plans_url(workspace, event, stage, f"{plan_id}/publish-rubric/"))
    plan = EvaluationPlan.objects.get(public_id=plan_id)
    Award.objects.create(
        event=event,
        name="Sponsor prize",
        evaluation_plan=plan,
        selection_source=SelectionSource.EVALUATION,
    )

    in_pool = cookie_client(Session.issue(judge_a).token).get(calendar_url(workspace, event)).json()
    assert len(in_pool["assignments"]) == 1

    not_in_pool = (
        cookie_client(Session.issue(judge_b).token).get(calendar_url(workspace, event)).json()
    )
    assert not_in_pool["assignments"] == []


def test_judge_workload_sorts_least_complete_first_and_omits_idle_judges():
    workspace, event, stage, project, organizer, judge_a, judge_b = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    plan_id = make_all_judges_plan(organizer_client, workspace, event, stage)
    submit_ballot(
        cookie_client(Session.issue(judge_a).token), workspace, event, stage, plan_id, project
    )

    rows = organizer_client.get(workload_url(workspace, event)).json()
    assert [row["judge"] for row in rows] == ["judge_b", "judge_a"]
    assert rows[0]["completion_ratio"] == 0.0
    assert rows[1]["completion_ratio"] == 1.0


def test_participant_cannot_read_calendar_or_workload():
    workspace, event, stage, project, organizer, judge_a, judge_b = make_fixture()
    participant = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(user=participant, workspace=workspace, role=Role.PARTICIPANT)
    participant_client = cookie_client(Session.issue(participant).token)

    assert participant_client.get(calendar_url(workspace, event)).status_code == 403
    assert participant_client.get(workload_url(workspace, event)).status_code == 403


def test_judge_cannot_read_the_organizer_workload_view():
    workspace, event, stage, project, organizer, judge_a, judge_b = make_fixture()
    judge_client = cookie_client(Session.issue(judge_a).token)
    assert judge_client.get(workload_url(workspace, event)).status_code == 403
