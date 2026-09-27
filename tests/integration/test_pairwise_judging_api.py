import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from django.test import Client
from evaluations.models import ConflictOfInterest, EvaluationPlan, PairwiseComparison
from events.models import Event
from projects.models import Project, Submission
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def cookie_client(token):
    client = Client()
    client.cookies["session"] = token
    return client


def make_fixture(project_count=3):
    organizer = User.objects.create_user(username="organizer", password="unused")
    judge_a = User.objects.create_user(username="judge_a", password="unused")
    judge_b = User.objects.create_user(username="judge_b", password="unused")
    participant = User.objects.create_user(username="member", password="unused")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge_a, workspace=workspace, role=Role.JUDGE)
    Membership.objects.create(user=judge_b, workspace=workspace, role=Role.JUDGE)
    Membership.objects.create(user=participant, workspace=workspace, role=Role.PARTICIPANT)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    stage = Stage.objects.create(event=event, name="Finals")
    projects = []
    for i in range(project_count):
        project = Project.objects.create(event=event, name=f"Project {i}", created_by=organizer)
        Submission.objects.create(project=project, stage=stage, updated_by=organizer)
        projects.append(project)
    plan = EvaluationPlan.objects.create(stage=stage, name="Pairwise panel", mode="pairwise")
    return workspace, event, stage, plan, organizer, judge_a, judge_b, participant, projects


def url(workspace, event, stage, plan, suffix=""):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/{plan.public_id}/{suffix}"
    )


def submit(client, workspace, event, stage, plan, project_a, project_b, winner=None):
    return client.post(
        url(workspace, event, stage, plan, "pairwise/comparisons/"),
        data={
            "project_a": str(project_a.public_id),
            "project_b": str(project_b.public_id),
            "winner": str(winner.public_id) if winner else None,
        },
        content_type="application/json",
    )


def test_judge_submits_a_comparison_and_it_is_stored_in_canonical_order():
    workspace, event, stage, plan, organizer, judge_a, _, _, projects = make_fixture()
    client = cookie_client(Session.issue(judge_a).token)
    # Submit with the higher-pk project first; storage must still canonicalize.
    response = submit(client, workspace, event, stage, plan, projects[1], projects[0], projects[0])
    assert response.status_code == 201
    comparison = PairwiseComparison.objects.get()
    assert comparison.project_a_id == projects[0].id
    assert comparison.project_b_id == projects[1].id
    assert comparison.winner_id == projects[0].id
    assert AuditEvent.objects.filter(action="pairwise_comparison.submitted").count() == 1


def test_a_tie_is_accepted_with_a_null_winner():
    workspace, event, stage, plan, _, judge_a, _, _, projects = make_fixture()
    client = cookie_client(Session.issue(judge_a).token)
    response = submit(client, workspace, event, stage, plan, projects[0], projects[1])
    assert response.status_code == 201
    assert response.json()["winner"] is None


def test_duplicate_comparison_in_either_order_is_rejected():
    workspace, event, stage, plan, _, judge_a, _, _, projects = make_fixture()
    client = cookie_client(Session.issue(judge_a).token)
    first = submit(client, workspace, event, stage, plan, projects[0], projects[1], projects[0])
    assert first.status_code == 201
    dupe = submit(client, workspace, event, stage, plan, projects[1], projects[0], projects[1])
    assert dupe.status_code == 400


def test_a_judge_cannot_compare_the_same_project_against_itself():
    workspace, event, stage, plan, _, judge_a, _, _, projects = make_fixture()
    client = cookie_client(Session.issue(judge_a).token)
    response = submit(client, workspace, event, stage, plan, projects[0], projects[0])
    assert response.status_code == 400


def test_conflict_of_interest_blocks_a_comparison():
    workspace, event, stage, plan, organizer, judge_a, _, _, projects = make_fixture()
    ConflictOfInterest.objects.create(
        event=event, judge=judge_a, project=projects[0], declared_by=organizer
    )
    client = cookie_client(Session.issue(judge_a).token)
    response = submit(client, workspace, event, stage, plan, projects[0], projects[1], projects[1])
    assert response.status_code == 400


def test_judge_cannot_see_a_peers_comparisons_but_organizer_sees_all():
    workspace, event, stage, plan, organizer, judge_a, judge_b, _, projects = make_fixture()
    judge_a_client = cookie_client(Session.issue(judge_a).token)
    submit(judge_a_client, workspace, event, stage, plan, projects[0], projects[1], projects[0])

    judge_b_client = cookie_client(Session.issue(judge_b).token)
    assert (
        judge_b_client.get(url(workspace, event, stage, plan, "pairwise/comparisons/")).json() == []
    )

    organizer_client = cookie_client(Session.issue(organizer).token)
    organizer_view = organizer_client.get(
        url(workspace, event, stage, plan, "pairwise/comparisons/")
    ).json()
    assert len(organizer_view) == 1


def test_rubric_ballot_submission_is_rejected_on_a_pairwise_mode_plan():
    workspace, event, stage, plan, _, judge_a, _, _, projects = make_fixture()
    client = cookie_client(Session.issue(judge_a).token)
    response = client.post(
        url(workspace, event, stage, plan, "ballots/"),
        data={"project": str(projects[0].public_id), "responses": []},
        content_type="application/json",
    )
    assert response.status_code == 400


def test_pairwise_comparison_is_rejected_on_a_rubric_mode_plan():
    workspace, event, stage, plan, _, judge_a, _, _, projects = make_fixture()
    plan.mode = "rubric"
    plan.save(update_fields=["mode"])
    client = cookie_client(Session.issue(judge_a).token)
    response = submit(client, workspace, event, stage, plan, projects[0], projects[1], projects[0])
    assert response.status_code == 400


def test_next_pair_balances_coverage_and_returns_null_once_exhausted():
    workspace, event, stage, plan, _, judge_a, _, _, projects = make_fixture(project_count=3)
    client = cookie_client(Session.issue(judge_a).token)
    next_url = url(workspace, event, stage, plan, "pairwise/next/")

    seen_pairs = set()
    for _ in range(3):  # 3 candidates -> exactly 3 possible pairs
        pair = client.get(next_url).json()
        assert pair is not None
        key = frozenset((pair["project_a"], pair["project_b"]))
        assert key not in seen_pairs
        seen_pairs.add(key)
        submit_response = client.post(
            url(workspace, event, stage, plan, "pairwise/comparisons/"),
            data={"project_a": pair["project_a"], "project_b": pair["project_b"], "winner": None},
            content_type="application/json",
        )
        assert submit_response.status_code == 201

    assert client.get(next_url).json() is None


def test_compute_run_publish_and_read_ranked_results():
    workspace, event, stage, plan, organizer, judge_a, _, participant, projects = make_fixture()
    judge_client = cookie_client(Session.issue(judge_a).token)
    # Project 0 beats both others; project 1 beats project 2.
    submit(judge_client, workspace, event, stage, plan, projects[0], projects[1], projects[0])
    submit(judge_client, workspace, event, stage, plan, projects[0], projects[2], projects[0])
    submit(judge_client, workspace, event, stage, plan, projects[1], projects[2], projects[1])

    organizer_client = cookie_client(Session.issue(organizer).token)
    run_response = organizer_client.post(url(workspace, event, stage, plan, "pairwise/runs/"))
    assert run_response.status_code == 201
    run_body = run_response.json()
    assert run_body["number"] == 1
    assert run_body["converged"] is True

    publish = organizer_client.post(
        url(workspace, event, stage, plan, "pairwise/publish-results/"),
        data={"pairwise_run": run_body["public_id"]},
        content_type="application/json",
    )
    assert publish.status_code == 200

    # Not visible to a participant until the organizer opts in.
    participant_client = cookie_client(Session.issue(participant).token)
    assert (
        participant_client.get(url(workspace, event, stage, plan, "pairwise/results/")).status_code
        == 403
    )

    results = organizer_client.get(url(workspace, event, stage, plan, "pairwise/results/")).json()
    assert [r["project"] for r in results] == [
        str(projects[0].public_id),
        str(projects[1].public_id),
        str(projects[2].public_id),
    ]
    assert results[0]["strength"] > results[1]["strength"] > results[2]["strength"]

    csv_response = organizer_client.get(url(workspace, event, stage, plan, "pairwise/results.csv"))
    assert csv_response.status_code == 200
    assert b"Project 0" in csv_response.content


def test_normalization_run_is_rejected_on_a_pairwise_mode_plan():
    workspace, event, stage, plan, organizer, _, _, _, _ = make_fixture()
    client = cookie_client(Session.issue(organizer).token)
    response = client.post(url(workspace, event, stage, plan, "normalization-runs/"))
    assert response.status_code == 400
