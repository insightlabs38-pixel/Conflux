import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.models import BallotDraft, EvaluationPlan
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


def make_fixture():
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
    for i in range(2):
        project = Project.objects.create(event=event, name=f"Project {i}", created_by=organizer)
        Submission.objects.create(project=project, stage=stage, updated_by=organizer)
        projects.append(project)
    plan = EvaluationPlan.objects.create(stage=stage, name="Panel", draft_criteria=CRITERIA)
    return workspace, event, stage, plan, organizer, judge_a, judge_b, participant, projects


def url(workspace, event, stage, plan, suffix=""):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/{plan.public_id}/{suffix}"
    )


def draft_url(workspace, event, stage, plan, project):
    return url(workspace, event, stage, plan, f"ballots/{project.public_id}/draft/")


def test_ballot_draft_autosaves_partial_state_and_is_private_to_the_judge():
    workspace, event, stage, plan, _, judge_a, judge_b, _, projects = make_fixture()
    judge_a_client = cookie_client(Session.issue(judge_a).token)
    saved = judge_a_client.put(
        draft_url(workspace, event, stage, plan, projects[0]),
        data={"responses": {"impact": 7}, "comment": "still thinking"},
        content_type="application/json",
    )
    assert saved.status_code == 200
    assert saved.json()["responses"] == {"impact": 7}

    reloaded = judge_a_client.get(draft_url(workspace, event, stage, plan, projects[0]))
    assert reloaded.json()["comment"] == "still thinking"

    # A second PUT overwrites (upsert), it doesn't create a second row.
    judge_a_client.put(
        draft_url(workspace, event, stage, plan, projects[0]),
        data={"responses": {"impact": 9}, "comment": "final answer"},
        content_type="application/json",
    )
    assert BallotDraft.objects.filter(judge=judge_a, project=projects[0]).count() == 1

    judge_b_client = cookie_client(Session.issue(judge_b).token)
    assert judge_b_client.get(draft_url(workspace, event, stage, plan, projects[0])).json() is None


def test_submitting_a_ballot_clears_its_draft():
    workspace, event, stage, plan, organizer, judge_a, _, _, projects = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    organizer_client.post(url(workspace, event, stage, plan, "publish-rubric/"))
    judge_client = cookie_client(Session.issue(judge_a).token)
    judge_client.put(
        draft_url(workspace, event, stage, plan, projects[0]),
        data={"responses": {"impact": 7}},
        content_type="application/json",
    )
    judge_client.post(
        url(workspace, event, stage, plan, "ballots/"),
        data={
            "project": str(projects[0].public_id),
            "responses": [{"criterion_id": "impact", "score": 7}],
        },
        content_type="application/json",
    )
    assert not BallotDraft.objects.filter(judge=judge_a, project=projects[0]).exists()


def test_own_and_peer_ballot_isolation_mirrors_checker_semantics():
    workspace, event, stage, plan, organizer, judge_a, judge_b, _, projects = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    organizer_client.post(url(workspace, event, stage, plan, "publish-rubric/"))
    ballots_url = url(workspace, event, stage, plan, "ballots/")
    judge_a_client = cookie_client(Session.issue(judge_a).token)
    judge_a_client.post(
        ballots_url,
        data={
            "project": str(projects[0].public_id),
            "responses": [{"criterion_id": "impact", "score": 5}],
        },
        content_type="application/json",
    )

    own = judge_a_client.get(ballots_url + f"?judge={judge_a.public_id}")
    assert own.status_code == 200 and len(own.json()) == 1

    judge_b_client = cookie_client(Session.issue(judge_b).token)
    peer = judge_b_client.get(ballots_url + f"?judge={judge_a.public_id}")
    assert peer.status_code == 403

    organizer_view = organizer_client.get(ballots_url + f"?judge={judge_a.public_id}")
    assert organizer_view.status_code == 200 and len(organizer_view.json()) == 1


def test_progress_reports_expected_and_submitted_ballots_and_is_organizer_only():
    workspace, event, stage, plan, organizer, judge_a, judge_b, participant, projects = (
        make_fixture()
    )
    organizer_client = cookie_client(Session.issue(organizer).token)
    organizer_client.post(url(workspace, event, stage, plan, "publish-rubric/"))
    from evaluations.models import EvaluationPool, PoolMembership

    pool = EvaluationPool.objects.create(event=event, name="Main")
    PoolMembership.objects.create(pool=pool, judge=judge_a)
    PoolMembership.objects.create(pool=pool, judge=judge_b)
    plan.pool = pool
    plan.save()

    progress_url = url(workspace, event, stage, plan, "progress/")
    before = organizer_client.get(progress_url).json()
    assert before["candidate_count"] == 2
    assert before["expected_ballots"] == 4  # 2 judges x 2 projects, all_judges default
    assert before["submitted_ballots"] == 0

    judge_a_client = cookie_client(Session.issue(judge_a).token)
    judge_a_client.post(
        url(workspace, event, stage, plan, "ballots/"),
        data={
            "project": str(projects[0].public_id),
            "responses": [{"criterion_id": "impact", "score": 5}],
        },
        content_type="application/json",
    )
    after = organizer_client.get(progress_url).json()
    assert after["submitted_ballots"] == 1
    assert after["completion_ratio"] == pytest.approx(0.25)

    participant_client = cookie_client(Session.issue(participant).token)
    assert participant_client.get(progress_url).status_code == 403


def test_results_are_404_until_published_then_visible_per_the_participant_flag():
    workspace, event, stage, plan, organizer, judge_a, judge_b, participant, projects = (
        make_fixture()
    )
    organizer_client = cookie_client(Session.issue(organizer).token)
    organizer_client.post(url(workspace, event, stage, plan, "publish-rubric/"))
    ballots_url = url(workspace, event, stage, plan, "ballots/")
    cookie_client(Session.issue(judge_a).token).post(
        ballots_url,
        data={
            "project": str(projects[0].public_id),
            "responses": [{"criterion_id": "impact", "score": 9}],
        },
        content_type="application/json",
    )
    cookie_client(Session.issue(judge_b).token).post(
        ballots_url,
        data={
            "project": str(projects[1].public_id),
            "responses": [{"criterion_id": "impact", "score": 2}],
        },
        content_type="application/json",
    )

    results_url = url(workspace, event, stage, plan, "results/")
    assert organizer_client.get(results_url).status_code == 404

    run = organizer_client.post(
        url(workspace, event, stage, plan, "normalization-runs/"),
        data={"ridge_lambda": 0},
        content_type="application/json",
    ).json()
    published = organizer_client.post(
        url(workspace, event, stage, plan, "publish-results/"),
        data={"normalization_run": run["public_id"]},
        content_type="application/json",
    )
    assert published.status_code == 200

    ranked = organizer_client.get(results_url).json()
    assert [r["rank"] for r in ranked] == [1, 2]
    assert ranked[0]["project"] == str(projects[0].public_id)

    participant_client = cookie_client(Session.issue(participant).token)
    assert participant_client.get(results_url).status_code == 403

    plan.refresh_from_db()
    plan.results_visible_to_participants = True
    plan.save()
    assert participant_client.get(results_url).status_code == 200

    csv_response = organizer_client.get(url(workspace, event, stage, plan, "results.csv"))
    assert csv_response.status_code == 200
    body = csv_response.content.decode()
    assert "Project 0" in body and "Project 1" in body


def test_publish_results_rejects_a_normalization_run_from_another_plan():
    workspace, event, stage, plan, organizer, judge_a, _, _, projects = make_fixture()
    other_plan = EvaluationPlan.objects.create(stage=stage, name="Other", draft_criteria=CRITERIA)
    organizer_client = cookie_client(Session.issue(organizer).token)
    organizer_client.post(url(workspace, event, stage, other_plan, "publish-rubric/"))
    other_run = organizer_client.post(
        url(workspace, event, stage, other_plan, "normalization-runs/"),
        data={},
        content_type="application/json",
    ).json()

    response = organizer_client.post(
        url(workspace, event, stage, plan, "publish-results/"),
        data={"normalization_run": other_run["public_id"]},
        content_type="application/json",
    )
    assert response.status_code == 404


def test_candidate_queue_lists_pending_drafted_and_submitted_and_excludes_conflicts():
    workspace, event, stage, plan, organizer, judge_a, _, _, projects = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    organizer_client.post(url(workspace, event, stage, plan, "publish-rubric/"))
    organizer_client.post(
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/judge-conflicts/",
        data={"judge": str(judge_a.public_id), "project": str(projects[1].public_id)},
        content_type="application/json",
    )

    judge_client = cookie_client(Session.issue(judge_a).token)
    judge_client.put(
        draft_url(workspace, event, stage, plan, projects[0]),
        data={"responses": {"impact": 3}},
        content_type="application/json",
    )

    queue = judge_client.get(url(workspace, event, stage, plan, "candidates/")).json()
    assert len(queue) == 1  # projects[1] excluded by the declared conflict
    assert queue[0]["project"] == str(projects[0].public_id)
    assert queue[0]["status"] == "drafted"

    judge_client.post(
        url(workspace, event, stage, plan, "ballots/"),
        data={
            "project": str(projects[0].public_id),
            "responses": [{"criterion_id": "impact", "score": 3}],
        },
        content_type="application/json",
    )
    after = judge_client.get(url(workspace, event, stage, plan, "candidates/")).json()
    assert after[0]["status"] == "submitted"


def test_candidate_queue_under_assigned_subset_is_scoped_to_the_active_assignment():
    workspace, event, stage, plan, organizer, judge_a, judge_b, _, projects = make_fixture()
    from evaluations.models import EvaluationPool, EvaluationPoolStrategy, PoolMembership

    pool = EvaluationPool.objects.create(event=event, name="Main")
    PoolMembership.objects.create(pool=pool, judge=judge_a)
    PoolMembership.objects.create(pool=pool, judge=judge_b)
    plan.pool = pool
    plan.pool_strategy = EvaluationPoolStrategy.ASSIGNED_SUBSET
    plan.save()

    organizer_client = cookie_client(Session.issue(organizer).token)
    organizer_client.post(url(workspace, event, stage, plan, "publish-rubric/"))

    judge_a_client = cookie_client(Session.issue(judge_a).token)
    assert judge_a_client.get(url(workspace, event, stage, plan, "candidates/")).json() == []

    organizer_client.post(
        url(workspace, event, stage, plan, "assignments/activate/"),
        data={"coverage": 1},
        content_type="application/json",
    )
    queue = judge_a_client.get(url(workspace, event, stage, plan, "candidates/")).json()
    # Coverage=1 assigns judge_a at least one candidate; C-B15's connectivity
    # repair may deterministically add a second shared candidate to bridge
    # the judge-overlap graph, so this isn't necessarily exactly one.
    assert 1 <= len(queue) <= len(projects)


def test_judges_can_read_stages_plans_and_the_current_rubric_but_not_write():
    workspace, event, stage, plan, organizer, judge_a, _, _, _ = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    organizer_client.post(url(workspace, event, stage, plan, "publish-rubric/"))

    judge_client = cookie_client(Session.issue(judge_a).token)
    stages_url = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/stages/"
    assert judge_client.get(stages_url).status_code == 200
    assert (
        judge_client.post(stages_url, {"name": "x"}, content_type="application/json").status_code
        == 403
    )

    plans_url = f"{stages_url}{stage.public_id}/evaluation-plans/"
    assert judge_client.get(plans_url).status_code == 200
    assert (
        judge_client.post(plans_url, {"name": "x"}, content_type="application/json").status_code
        == 403
    )

    rubric_url = url(workspace, event, stage, plan, "publish-rubric/")
    read = judge_client.get(rubric_url)
    assert read.status_code == 200
    assert read.json()["number"] == 1
    assert judge_client.post(rubric_url).status_code == 403


def test_rubric_read_returns_a_parseable_null_before_anything_is_published():
    workspace, event, stage, plan, _, judge_a, _, _, _ = make_fixture()
    judge_client = cookie_client(Session.issue(judge_a).token)
    response = judge_client.get(url(workspace, event, stage, plan, "publish-rubric/"))
    assert response.status_code == 200
    assert response.json() is None
