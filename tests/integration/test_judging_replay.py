import pytest
from accounts.models import User
from evaluations import pairwise as pairwise_module
from evaluations.models import (
    Ballot,
    BallotResponse,
    EvaluationPlan,
    NormalizationRun,
    PairwiseComparison,
)
from integrations.demo_scenarios import generate_demo_event
from test_sponsor_portal import client_for

pytestmark = pytest.mark.django_db


def world(seed=91, participants=6, judges=3):
    event = generate_demo_event(seed=seed, participants=participants, judges=judges)
    plan = EvaluationPlan.objects.get(stage__event=event)
    run = NormalizationRun.objects.get(plan=plan)
    prefix = f"demo-hackathon-{seed}-"
    return event, plan, run, {
        "org": User.objects.get(username=prefix + "organizer"),
        "judge": User.objects.get(username=prefix + "judge-01"),
        "part": User.objects.get(username=prefix + "participant-01"),
    }  # fmt: skip


def url(event, plan, run, query=""):
    return (
        f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}/stages/"
        f"{plan.stage.public_id}/evaluation-plans/{plan.public_id}/runs/{run.public_id}/replay/{query}"
    )


def failed(report):
    return {c["name"] for c in report["checks"] if not c["ok"]}


def test_untouched_run_replays_exactly_and_deterministically():
    event, plan, run, users = world()
    org = client_for(users["org"])
    first = org.get(url(event, plan, run)).json()
    assert first["verdict"] == "verified" and failed(first) == set()
    assert first["published"] is True and first["inputs"]["ballots"] == 18
    assert first["algorithm"] == "additive-ridge-gauss-seidel/1"
    assert org.get(url(event, plan, run)).json() == first
    assert len(first["report_digest"]) == 64 and len(first["inputs"]["digest"]) == 64


def test_timeline_shows_the_ranking_emerging_and_ends_at_the_published_leader():
    event, plan, run, users = world()
    report = client_for(users["org"]).get(url(event, plan, run, "?timeline=true")).json()
    points = report["timeline"]
    assert 1 < len(points) <= 20 and points[-1]["ballots"] == 18
    assert [p["ballots"] for p in points] == sorted({p["ballots"] for p in points})
    published_leader = plan.published_normalization_run.evidence["projects"]
    best = max(published_leader.items(), key=lambda kv: kv[1]["final"])[0]
    from projects.models import Project

    assert points[-1]["top"][0]["project"] == str(Project.objects.get(pk=int(best)).public_id)
    assert client_for(users["org"]).get(url(event, plan, run, "?timeline=maybe")).status_code == 400


def test_changed_ballots_missing_ballots_and_omissions_are_detected():
    event, plan, run, users = world()
    org = client_for(users["org"])
    response = BallotResponse.objects.filter(ballot__rubric_version__plan=plan).first()
    BallotResponse.objects.filter(pk=response.pk).update(score=response.score - 1)
    report = org.get(url(event, plan, run)).json()
    assert report["verdict"] == "mismatch" and failed(report) == {"ballots_unchanged"}
    BallotResponse.objects.filter(pk=response.pk).update(score=response.score)
    victim = Ballot.objects.filter(rubric_version__plan=plan).first()
    Ballot.objects.filter(pk=victim.pk).delete()
    assert failed(org.get(url(event, plan, run)).json()) >= {"ballots_exist"}


def test_altered_stored_results_fail_the_solver_and_ranking_checks():
    event, plan, run, users = world()
    evidence = run.evidence
    top = max(evidence["projects"], key=lambda k: evidence["projects"][k]["final"])
    evidence["projects"][top]["final"] += 5
    NormalizationRun.objects.filter(pk=run.pk).update(evidence=evidence)
    report = client_for(users["org"]).get(url(event, plan, run)).json()
    assert report["verdict"] == "mismatch" and "project_scores" in failed(report)
    NormalizationRun.objects.filter(pk=run.pk).update(grand_mean=run.grand_mean + 1)
    assert "grand_mean" in failed(client_for(users["org"]).get(url(event, plan, run)).json())


def test_ballots_that_predate_the_run_but_were_left_out_are_reported():
    event, plan, run, users = world()
    evidence = run.evidence
    dropped = evidence["ballots"].pop()
    NormalizationRun.objects.filter(pk=run.pk).update(evidence=evidence)
    report = client_for(users["org"]).get(url(event, plan, run)).json()
    assert "no_ballots_omitted" in failed(report)
    assert dropped["ballot"] in next(
        c["detail"] for c in report["checks"] if c["name"] == "no_ballots_omitted"
    )


def test_only_organizers_replay_and_runs_are_scoped_to_their_plan():
    event, plan, run, users = world()
    for name in ("judge", "part"):
        assert client_for(users[name]).get(url(event, plan, run)).status_code == 403
    other_event, other_plan, other_run, _ = world(seed=92, participants=3, judges=2)
    org = client_for(users["org"])
    assert org.get(url(event, plan, other_run)).status_code == 404
    unknown = type("R", (), {"public_id": "00000000-0000-4000-8000-000000000000"})
    assert org.get(url(event, plan, unknown)).status_code == 404


def test_pairwise_runs_replay_from_the_comparisons_recorded_before_them():
    event, plan, _, users = world()
    plan.mode = "pairwise"
    plan.save()
    projects = list(event.projects.order_by("pk"))[:4]
    judge = users["judge"]
    pairs = [(0, 1), (1, 2), (2, 3), (0, 2), (1, 3), (0, 3)]
    for index, (a, b) in enumerate(pairs):
        PairwiseComparison.objects.create(
            plan=plan,
            judge=judge,
            project_a=projects[a],
            project_b=projects[b],
            winner=projects[a] if index % 3 else projects[b],
        )
    run = pairwise_module.run(plan)
    org = client_for(users["org"])
    report = org.get(url(event, plan, run)).json()
    assert report["mode"] == "pairwise" and report["verdict"] == "verified"
    assert report["inputs"]["comparisons"] == 6
    PairwiseComparison.objects.filter(pk=PairwiseComparison.objects.first().pk).update(winner=None)
    assert org.get(url(event, plan, run)).json()["verdict"] == "mismatch"
