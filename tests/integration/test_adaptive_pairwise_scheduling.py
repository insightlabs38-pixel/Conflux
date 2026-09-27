import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.models import EvaluationPlan
from evaluations.pairwise import FAIRNESS_SLACK, select_next_pair
from events.models import Event
from projects.models import Project, Submission
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def cookie_client(token):
    client = Client()
    client.cookies["session"] = token
    return client


def make_fixture(project_count=4):
    organizer = User.objects.create_user(username="organizer", password="unused")
    judge_a = User.objects.create_user(username="judge_a", password="unused")
    judge_b = User.objects.create_user(username="judge_b", password="unused")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge_a, workspace=workspace, role=Role.JUDGE)
    Membership.objects.create(user=judge_b, workspace=workspace, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    stage = Stage.objects.create(event=event, name="Finals")
    projects = []
    for i in range(project_count):
        project = Project.objects.create(event=event, name=f"Project {i}", created_by=organizer)
        Submission.objects.create(project=project, stage=stage, updated_by=organizer)
        projects.append(project)
    plan = EvaluationPlan.objects.create(stage=stage, name="Pairwise panel", mode="pairwise")
    return workspace, event, stage, plan, organizer, judge_a, judge_b, projects


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


# --- pure function tests -------------------------------------------------


def test_with_no_strengths_it_falls_back_to_minimal_load_exactly_like_before():
    pair = select_next_pair(
        candidate_ids=[1, 2, 3],
        already_compared=set(),
        comparison_counts={1: 2, 2: 0, 3: 0},
        strengths=None,
    )
    assert pair == (2, 3)  # the only pair excluding the heavily-loaded id 1


def test_with_strengths_it_prefers_the_closest_pair_over_a_lower_load_pair():
    # (1,2) is tied in load with everything else being higher, but (1,3)
    # has strictly lower load -- pure load-based scheduling would pick
    # (1,3). Strength-aware scheduling should pick (1,2) instead: its
    # strengths are identical (uncertainty 0), the most informative
    # comparison to run, while still inside the fairness window.
    pair = select_next_pair(
        candidate_ids=[1, 2, 3],
        already_compared=set(),
        comparison_counts={1: 2, 2: 2, 3: 1},
        strengths={1: 5.0, 2: 5.0, 3: 1.0},
    )
    assert pair == (1, 2)


def test_fairness_slack_excludes_a_badly_over_compared_candidate_from_the_fair_pool():
    # id 3's strength is a perfect match for id 1 (uncertainty 0 -- the
    # single most informative pair overall), but id 3 already has far
    # more comparisons than the field minimum plus slack allows, so it
    # must be excluded and the pool falls back to the only remaining
    # option, (1, 2), even though that pair is far less uncertain.
    pair = select_next_pair(
        candidate_ids=[1, 2, 3],
        already_compared=set(),
        comparison_counts={1: 0, 2: 0, 3: 10},
        strengths={1: 1.0, 2: 100.0, 3: 1.0},
    )
    assert pair == (1, 2)


def test_a_pair_already_judged_by_this_judge_is_never_offered_again():
    assert (
        select_next_pair(
            candidate_ids=[1, 2],
            already_compared={(1, 2)},
            comparison_counts={1: 0, 2: 0},
            strengths={1: 1.0, 2: 1.0},
        )
        is None
    )


def test_fewer_than_two_candidates_returns_none():
    assert select_next_pair([1], set(), {}, None) is None
    assert select_next_pair([], set(), {}, None) is None


def test_fairness_slack_constant_is_a_small_positive_bound():
    # Documents the intended tuning: enough room for the uncertainty
    # signal to matter, not so much that coverage can drift badly.
    assert 0 < FAIRNESS_SLACK <= 2


# --- end-to-end API test --------------------------------------------------


def test_next_pair_prefers_the_run_s_closest_strengths_over_pure_coverage():
    workspace, event, stage, plan, organizer, judge_a, judge_b, projects = make_fixture(
        project_count=4
    )
    p0, p1, p2, p3 = projects
    judge_a_client = cookie_client(Session.issue(judge_a).token)

    # A full round by judge A: p2 beats everyone, p3 loses to everyone,
    # p0/p1 tie each other and split identically against p2/p3 -- an
    # exactly symmetric setup, so p0 and p1 must land on equal strength.
    submit(judge_a_client, workspace, event, stage, plan, p0, p1)  # tie
    submit(judge_a_client, workspace, event, stage, plan, p0, p2, p2)
    submit(judge_a_client, workspace, event, stage, plan, p0, p3, p0)
    submit(judge_a_client, workspace, event, stage, plan, p1, p2, p2)
    submit(judge_a_client, workspace, event, stage, plan, p1, p3, p1)
    submit(judge_a_client, workspace, event, stage, plan, p2, p3, p2)

    organizer_client = cookie_client(Session.issue(organizer).token)
    run_response = organizer_client.post(url(workspace, event, stage, plan, "pairwise/runs/"))
    assert run_response.status_code == 201
    strengths = {
        int(project_id): data["strength"]
        for project_id, data in run_response.json()["evidence"]["projects"].items()
    }
    assert strengths[p0.id] == pytest.approx(strengths[p1.id])

    judge_b_client = cookie_client(Session.issue(judge_b).token)
    # judge_b redundantly re-judges p0 vs p2 (allowed -- different judge),
    # so pure comparison-count load would now prefer p1-vs-p3 (the least
    # loaded remaining pair) over p0-vs-p1.
    submit(judge_b_client, workspace, event, stage, plan, p0, p2, p2)

    pair = judge_b_client.get(url(workspace, event, stage, plan, "pairwise/next/")).json()
    assert {pair["project_a"], pair["project_b"]} == {str(p0.public_id), str(p1.public_id)}


def test_next_pair_falls_back_to_coverage_before_any_run_exists():
    workspace, event, stage, plan, organizer, judge_a, judge_b, projects = make_fixture(
        project_count=3
    )
    p0, p1, p2 = projects
    judge_a_client = cookie_client(Session.issue(judge_a).token)
    submit(judge_a_client, workspace, event, stage, plan, p0, p1)

    judge_b_client = cookie_client(Session.issue(judge_b).token)
    pair = judge_b_client.get(url(workspace, event, stage, plan, "pairwise/next/")).json()
    # p2 has zero comparisons and p0/p1 have one each -- with no run yet
    # to inform an uncertainty preference, the least-loaded pair wins.
    assert str(p2.public_id) in (pair["project_a"], pair["project_b"])
