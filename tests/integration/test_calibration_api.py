import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from django.test import Client
from evaluations.models import Ballot, EvaluationPlan
from events.models import Event
from projects.models import Project, Submission
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

CRITERIA = [
    {"id": "impact", "name": "Impact", "weight": 1, "min_score": 0, "max_score": 10},
]


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

    calibration_project = Project.objects.create(
        event=event, name="Calibration sample", created_by=organizer
    )
    live_project = Project.objects.create(event=event, name="Real entry", created_by=organizer)
    Submission.objects.create(project=live_project, stage=stage, updated_by=organizer)

    plan = EvaluationPlan.objects.create(
        stage=stage, name="Panel", draft_criteria=CRITERIA, calibration_required=True
    )
    plan.calibration_projects.set([calibration_project])
    return (
        workspace,
        event,
        stage,
        plan,
        organizer,
        judge_a,
        judge_b,
        calibration_project,
        live_project,
    )


def url(workspace, event, stage, plan, suffix=""):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/{plan.public_id}/{suffix}"
    )


def publish_rubric(organizer_client, workspace, event, stage, plan):
    return organizer_client.post(url(workspace, event, stage, plan, "publish-rubric/"))


def submit_calibration(client, workspace, event, stage, plan, project, score=7):
    return client.post(
        url(workspace, event, stage, plan, "calibration/ballots/"),
        data={
            "project": str(project.public_id),
            "responses": [{"criterion_id": "impact", "score": score}],
        },
        content_type="application/json",
    )


def test_organizer_sets_calibration_projects():
    workspace, event, stage, plan, organizer, _, _, calibration_project, _ = make_fixture()
    client = cookie_client(Session.issue(organizer).token)
    response = client.put(
        url(workspace, event, stage, plan, "calibration-projects/"),
        data={"projects": [str(calibration_project.public_id)]},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert AuditEvent.objects.filter(action="calibration_projects.set").exists()


def test_judge_submits_a_calibration_ballot_and_it_is_marked_as_such():
    workspace, event, stage, plan, organizer, judge_a, _, calibration_project, _ = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    publish_rubric(organizer_client, workspace, event, stage, plan)

    client = cookie_client(Session.issue(judge_a).token)
    response = submit_calibration(client, workspace, event, stage, plan, calibration_project)
    assert response.status_code == 201
    ballot = Ballot.objects.get()
    assert ballot.is_calibration is True


def test_calibration_ballot_on_a_non_calibration_project_is_rejected():
    workspace, event, stage, plan, organizer, judge_a, _, _, live_project = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    publish_rubric(organizer_client, workspace, event, stage, plan)

    client = cookie_client(Session.issue(judge_a).token)
    response = submit_calibration(client, workspace, event, stage, plan, live_project)
    assert response.status_code == 400


def test_a_calibration_project_cannot_also_receive_a_live_ballot():
    workspace, event, stage, plan, organizer, judge_a, _, calibration_project, _ = make_fixture()
    # Make the calibration project a live candidate too, then try to ballot it for real.
    Submission.objects.create(project=calibration_project, stage=stage, updated_by=organizer)
    organizer_client = cookie_client(Session.issue(organizer).token)
    publish_rubric(organizer_client, workspace, event, stage, plan)
    plan.calibration_required = False
    plan.save(update_fields=["calibration_required"])

    client = cookie_client(Session.issue(judge_a).token)
    response = client.post(
        url(workspace, event, stage, plan, "ballots/"),
        data={
            "project": str(calibration_project.public_id),
            "responses": [{"criterion_id": "impact", "score": 5}],
        },
        content_type="application/json",
    )
    assert response.status_code == 400


def test_live_ballot_is_blocked_until_calibration_is_required_and_incomplete():
    workspace, event, stage, plan, organizer, judge_a, _, _, live_project = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    publish_rubric(organizer_client, workspace, event, stage, plan)

    client = cookie_client(Session.issue(judge_a).token)
    blocked = client.post(
        url(workspace, event, stage, plan, "ballots/"),
        data={
            "project": str(live_project.public_id),
            "responses": [{"criterion_id": "impact", "score": 5}],
        },
        content_type="application/json",
    )
    assert blocked.status_code == 400
    assert "calibration" in blocked.json()["detail"].lower()


def test_live_ballot_succeeds_once_calibration_is_complete():
    workspace, event, stage, plan, organizer, judge_a, _, calibration_project, live_project = (
        make_fixture()
    )
    organizer_client = cookie_client(Session.issue(organizer).token)
    publish_rubric(organizer_client, workspace, event, stage, plan)

    client = cookie_client(Session.issue(judge_a).token)
    assert (
        submit_calibration(client, workspace, event, stage, plan, calibration_project).status_code
        == 201
    )

    allowed = client.post(
        url(workspace, event, stage, plan, "ballots/"),
        data={
            "project": str(live_project.public_id),
            "responses": [{"criterion_id": "impact", "score": 5}],
        },
        content_type="application/json",
    )
    assert allowed.status_code == 201


def test_calibration_status_reflects_completion_and_isolates_judges():
    workspace, event, stage, plan, organizer, judge_a, judge_b, calibration_project, _ = (
        make_fixture()
    )
    organizer_client = cookie_client(Session.issue(organizer).token)
    publish_rubric(organizer_client, workspace, event, stage, plan)
    judge_a_client = cookie_client(Session.issue(judge_a).token)
    submit_calibration(judge_a_client, workspace, event, stage, plan, calibration_project)

    status_a = judge_a_client.get(url(workspace, event, stage, plan, "calibration/status/")).json()
    assert status_a["is_complete"] is True
    assert status_a["remaining"] == []

    judge_b_client = cookie_client(Session.issue(judge_b).token)
    status_b = judge_b_client.get(url(workspace, event, stage, plan, "calibration/status/")).json()
    assert status_b["is_complete"] is False
    assert status_b["remaining"] == [str(calibration_project.public_id)]

    # A judge cannot check another judge's status directly.
    denied = judge_b_client.get(
        url(workspace, event, stage, plan, "calibration/status/"),
        {"judge": str(judge_a.public_id)},
    )
    assert denied.status_code == 403

    # But the organizer can.
    organizer_view = organizer_client.get(
        url(workspace, event, stage, plan, "calibration/status/"),
        {"judge": str(judge_a.public_id)},
    ).json()
    assert organizer_view["is_complete"] is True


def test_calibration_summary_exposes_raw_per_judge_scores_and_spread():
    workspace, event, stage, plan, organizer, judge_a, judge_b, calibration_project, _ = (
        make_fixture()
    )
    organizer_client = cookie_client(Session.issue(organizer).token)
    publish_rubric(organizer_client, workspace, event, stage, plan)
    submit_calibration(
        cookie_client(Session.issue(judge_a).token),
        workspace,
        event,
        stage,
        plan,
        calibration_project,
        score=8,
    )
    submit_calibration(
        cookie_client(Session.issue(judge_b).token),
        workspace,
        event,
        stage,
        plan,
        calibration_project,
        score=2,
    )

    summary = organizer_client.get(
        url(workspace, event, stage, plan, "calibration/summary/")
    ).json()
    assert len(summary) == 1
    criterion = summary[0]["criteria"][0]
    assert criterion["criterion_id"] == "impact"
    assert criterion["min"] == 2
    assert criterion["max"] == 8
    assert criterion["spread"] == 6
    assert len(criterion["scores"]) == 2


def test_calibration_ballots_are_excluded_from_normalization_and_progress_counts():
    workspace, event, stage, plan, organizer, judge_a, _, calibration_project, live_project = (
        make_fixture()
    )
    organizer_client = cookie_client(Session.issue(organizer).token)
    publish_rubric(organizer_client, workspace, event, stage, plan)
    client = cookie_client(Session.issue(judge_a).token)
    submit_calibration(client, workspace, event, stage, plan, calibration_project)
    client.post(
        url(workspace, event, stage, plan, "ballots/"),
        data={
            "project": str(live_project.public_id),
            "responses": [{"criterion_id": "impact", "score": 5}],
        },
        content_type="application/json",
    )

    progress = organizer_client.get(url(workspace, event, stage, plan, "progress/")).json()
    assert progress["submitted_ballots"] == 1
    assert progress["calibration"]["project_count"] == 1
    assert progress["calibration"]["judges_complete"] == 1

    from evaluations.scoring import ballot_observations

    observations = ballot_observations(plan)
    assert len(observations) == 1
    assert observations[0][1] == live_project.id
