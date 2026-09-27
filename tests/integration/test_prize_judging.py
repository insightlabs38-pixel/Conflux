import pytest
from accounts.models import Session, User
from awards.models import Award
from django.test import Client
from evaluations.assignment import compute_assignment
from evaluations.models import Ballot, EvaluationPlan, EvaluationPool, PoolMembership
from events.models import Event, Track
from projects.models import Project, Submission
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

CRITERIA = [{"id": "impact", "name": "Impact", "weight": 1, "min_score": 0, "max_score": 10}]


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def setup_case():
    organizer = User.objects.create_user(username="organizer", password="unused")
    sponsor_judge = User.objects.create_user(username="sponsor", password="unused")
    other_judge = User.objects.create_user(username="other", password="unused")
    workspace = Workspace.objects.create(name="W", slug="w")
    for user, role in (
        (organizer, Role.ORGANIZER),
        (sponsor_judge, Role.JUDGE),
        (other_judge, Role.JUDGE),
    ):
        Membership.objects.create(user=user, workspace=workspace, role=role)
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    stage = Stage.objects.create(event=event, name="Final")
    track = Track.objects.create(event=event, name="Sponsor track")
    other_track = Track.objects.create(event=event, name="Other track")
    pool = EvaluationPool.objects.create(event=event, name="Sponsor judges")
    PoolMembership.objects.create(pool=pool, judge=sponsor_judge)
    projects = [
        Project.objects.create(event=event, name=name, track=project_track, created_by=organizer)
        for name, project_track in (
            ("Eligible", track),
            ("Wrong track", other_track),
            ("Unfinalized", track),
        )
    ]
    for project in projects:
        Submission.objects.create(
            project=project,
            stage=stage,
            status="draft" if project == projects[2] else "finalized",
            updated_by=organizer,
        )
    base = (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/stages/{stage.public_id}/evaluation-plans/"
    )
    organizer_client = client_for(organizer)
    response = organizer_client.post(
        base,
        data={
            "name": "Sponsor prize panel",
            "pool": str(pool.public_id),
            "prize_judging": True,
            "draft_criteria": CRITERIA,
        },
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    plan = EvaluationPlan.objects.get(public_id=response.json()["public_id"])
    return (
        organizer_client,
        client_for(sponsor_judge),
        client_for(other_judge),
        event,
        track,
        plan,
        projects,
        base,
    )


def test_prize_judging_uses_linked_award_scope_and_dedicated_pool():
    organizer, sponsor, outsider, event, track, plan, projects, base = setup_case()
    plan_url = f"{base}{plan.public_id}/"
    assert sponsor.get(plan_url + "candidates/").json() == []
    award_url = base.split("/stages/")[0] + "/awards/"
    created = organizer.post(
        award_url,
        data={
            "name": "Sponsor prize",
            "selection_source": "evaluation",
            "evaluation_plan": str(plan.public_id),
            "eligibility_track": str(track.public_id),
            "winner_count": 1,
        },
        content_type="application/json",
    )
    assert created.status_code == 201, created.content
    assert Award.objects.count() == 1
    queue = sponsor.get(plan_url + "candidates/")
    assert queue.status_code == 200
    assert [item["project"] for item in queue.json()] == [str(projects[0].public_id)]
    assert outsider.get(plan_url + "candidates/").json() == []
    assert {(pair.judge_id, pair.project_id) for pair in compute_assignment(plan)} == {
        (PoolMembership.objects.get(pool=plan.pool).judge_id, projects[0].id)
    }
    assert organizer.get(plan_url + "progress/").json()["candidate_count"] == 1

    assert organizer.post(plan_url + "publish-rubric/").status_code == 201
    ballot_url = plan_url + "ballots/"

    def ballot(project):
        return {
            "project": str(project.public_id),
            "responses": [{"criterion_id": "impact", "score": 7}],
        }

    assert (
        outsider.post(ballot_url, ballot(projects[0]), content_type="application/json").status_code
        == 400
    )
    assert (
        sponsor.post(ballot_url, ballot(projects[1]), content_type="application/json").status_code
        == 400
    )
    assert (
        sponsor.post(ballot_url, ballot(projects[2]), content_type="application/json").status_code
        == 400
    )
    assert (
        sponsor.post(ballot_url, ballot(projects[0]), content_type="application/json").status_code
        == 201
    )
    assert Ballot.objects.count() == 1

    duplicate = organizer.post(
        award_url,
        data={
            "name": "Another prize",
            "selection_source": "evaluation",
            "evaluation_plan": str(plan.public_id),
            "winner_count": 1,
        },
        content_type="application/json",
    )
    assert duplicate.status_code == 400
    assert Award.objects.count() == 1


def test_prize_plan_requires_pool_and_scope_is_immutable():
    organizer, _, _, _, _, plan, _, base = setup_case()
    response = organizer.post(
        base,
        data={"name": "No pool", "prize_judging": True},
        content_type="application/json",
    )
    assert response.status_code == 400
    changed = organizer.patch(
        f"{base}{plan.public_id}/",
        data={"prize_judging": False},
        content_type="application/json",
    )
    assert changed.status_code == 400
    other_pool = EvaluationPool.objects.create(event=plan.stage.event, name="Other pool")
    changed_pool = organizer.patch(
        f"{base}{plan.public_id}/",
        data={"pool": str(other_pool.public_id)},
        content_type="application/json",
    )
    assert changed_pool.status_code == 400
    plan.refresh_from_db()
    assert plan.prize_judging
    assert plan.pool_id != other_pool.id


def test_prize_award_must_be_linked_before_judging_evidence():
    organizer, _, _, _, _, plan, _, base = setup_case()
    assert organizer.post(f"{base}{plan.public_id}/publish-rubric/").status_code == 201
    plan.rubric_versions.first().ballots.create(
        judge=PoolMembership.objects.get(pool=plan.pool).judge,
        project=Project.objects.get(name="Eligible"),
    )
    award_url = base.split("/stages/")[0] + "/awards/"
    response = organizer.post(
        award_url,
        data={
            "name": "Late prize",
            "selection_source": "evaluation",
            "evaluation_plan": str(plan.public_id),
            "winner_count": 1,
        },
        content_type="application/json",
    )
    assert response.status_code == 400
    assert Award.objects.count() == 0


def test_prize_pairwise_comparisons_use_same_candidate_and_pool_scope():
    organizer, sponsor, outsider, event, track, plan, projects, base = setup_case()
    plan.mode = "pairwise"
    plan.save(update_fields=["mode"])
    projects[1].track = track
    projects[1].save(update_fields=["track"])
    award_url = base.split("/stages/")[0] + "/awards/"
    assert (
        organizer.post(
            award_url,
            data={
                "name": "Pairwise prize",
                "selection_source": "evaluation",
                "evaluation_plan": str(plan.public_id),
                "eligibility_track": str(track.public_id),
                "winner_count": 1,
            },
            content_type="application/json",
        ).status_code
        == 201
    )
    pair_url = f"{base}{plan.public_id}/pairwise/comparisons/"

    def compare(first, second):
        return {
            "project_a": str(first.public_id),
            "project_b": str(second.public_id),
            "winner": str(first.public_id),
        }

    assert (
        outsider.post(
            pair_url, compare(projects[0], projects[1]), content_type="application/json"
        ).status_code
        == 400
    )
    assert (
        sponsor.post(
            pair_url, compare(projects[0], projects[2]), content_type="application/json"
        ).status_code
        == 400
    )
    assert (
        sponsor.post(
            pair_url, compare(projects[0], projects[1]), content_type="application/json"
        ).status_code
        == 201
    )
