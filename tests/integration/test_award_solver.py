import pytest
from accounts.models import Session, User
from awards.models import Award, AwardWinner
from awards.services import select_winner
from awards.solver import propose_allocations
from django.test import Client
from django.utils import timezone
from evaluations.models import EvaluationPlan, NormalizationRun
from events.models import Event, Track
from projects.models import Project, Submission
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def setup_case():
    organizer = User.objects.create_user(username="organizer", password="unused")
    judge = User.objects.create_user(username="judge", password="unused")
    workspace = Workspace.objects.create(name="W", slug="w")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    track = Track.objects.create(event=event, name="Limited")
    projects = [
        Project.objects.create(event=event, created_by=organizer, name=name, track=project_track)
        for name, project_track in (("A", track), ("B", None))
    ]
    client = Client()
    client.cookies["session"] = Session.issue(organizer).token
    outsider = Client()
    outsider.cookies["session"] = Session.issue(judge).token
    url = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/awards/proposals/"
    return event, organizer, track, projects, client, outsider, url


def test_solver_fills_constrained_award_first_without_writing_winners():
    event, organizer, track, projects, client, outsider, url = setup_case()
    broad = Award.objects.create(
        event=event, name="Broad", require_finalized_submission=False, allow_stacking=False
    )
    limited = Award.objects.create(
        event=event,
        name="Limited",
        eligibility_track=track,
        require_finalized_submission=False,
    )
    assert outsider.get(url).status_code == 403
    response = client.get(url)
    assert response.status_code == 200
    by_award = {row["award"]: row for row in response.json()["awards"]}
    assert by_award[str(broad.public_id)]["proposed"] == [str(projects[1].public_id)]
    assert by_award[str(limited.public_id)]["proposed"] == [str(projects[0].public_id)]
    assert not response.json()["search_limited"]
    assert AwardWinner.objects.count() == 0
    select_winner(award=broad, project=projects[1], actor=organizer)
    select_winner(award=limited, project=projects[0], actor=organizer)
    assert AwardWinner.objects.count() == 2


def test_solver_respects_existing_winners_conflict_groups_and_publication():
    event, organizer, _, projects, client, _, url = setup_case()
    fixed = Award.objects.create(
        event=event,
        name="Fixed",
        require_finalized_submission=False,
        conflict_group="sponsor",
        published_at=timezone.now(),
    )
    AwardWinner.objects.create(
        award=fixed, project=projects[0], selected_by=organizer, source="manual"
    )
    other = Award.objects.create(
        event=event, name="Other", require_finalized_submission=False, conflict_group="sponsor"
    )
    rows = {row["award"]: row for row in client.get(url).json()["awards"]}
    assert rows[str(fixed.public_id)]["proposed"] == []
    assert rows[str(other.public_id)]["proposed"] == [str(projects[1].public_id)]
    assert AwardWinner.objects.count() == 1


def test_solver_excludes_unready_evaluation_and_finalization_ineligible_projects():
    event, _, _, projects, client, _, url = setup_case()
    stage = Stage.objects.create(event=event, name="Final")
    plan = EvaluationPlan.objects.create(stage=stage, name="Judging")
    evaluated = Award.objects.create(
        event=event, name="Evaluated", selection_source="evaluation", evaluation_plan=plan
    )
    manual = Award.objects.create(event=event, name="Manual")
    rows = {row["award"]: row for row in client.get(url).json()["awards"]}
    assert rows[str(evaluated.public_id)]["proposed"] == []
    assert rows[str(evaluated.public_id)]["blocker"]
    assert rows[str(evaluated.public_id)]["unfilled"] == 1
    assert rows[str(manual.public_id)]["proposed"] == []
    assert rows[str(manual.public_id)]["unfilled"] == 1


def test_solver_uses_published_rank_and_requires_no_override():
    event, organizer, _, projects, client, _, url = setup_case()
    stage = Stage.objects.create(event=event, name="Final")
    for project in projects:
        Submission.objects.create(
            project=project, stage=stage, status="finalized", updated_by=organizer
        )
    plan = EvaluationPlan.objects.create(stage=stage, name="Judging")
    run = NormalizationRun.objects.create(
        plan=plan,
        number=1,
        ridge_lambda=1.0,
        iterations=1,
        converged=True,
        grand_mean=3.0,
        evidence={
            "projects": {
                str(projects[0].id): {"raw": 4.0, "final": 4.0},
                str(projects[1].id): {"raw": 8.0, "final": 8.0},
            }
        },
    )
    plan.published_normalization_run = run
    plan.save(update_fields=["published_normalization_run"])
    award = Award.objects.create(
        event=event, name="Judged", selection_source="evaluation", evaluation_plan=plan
    )
    row = client.get(url).json()["awards"][0]
    assert row["award"] == str(award.public_id)
    assert row["proposed"] == [str(projects[1].public_id)]
    assert row["unfilled"] == 0


def test_solver_reports_search_limit_without_writing_partial_winners():
    event, _, _, _, _, _, _ = setup_case()
    Award.objects.create(event=event, name="Broad", require_finalized_submission=False)
    proposal = propose_allocations(event, max_nodes=1)
    assert proposal["search_limited"]
    assert AwardWinner.objects.count() == 0
