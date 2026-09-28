import pytest
from accounts.models import User
from audit.models import AuditEvent, DomainEvent
from awards.models import Award, AwardWinner
from awards.services import select_winner
from django.core.exceptions import ValidationError
from evaluations.models import EvaluationPlan, NormalizationRun
from events.models import Event, Track
from projects.models import Project, Submission
from stages.models import Stage
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def setup_case():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    actor = User.objects.create_user(username="organizer", password="unused")
    track = Track.objects.create(event=event, name="T")
    projects = [
        Project.objects.create(event=event, created_by=actor, name=f"Project {index}", track=track)
        for index in range(3)
    ]
    return event, actor, track, projects


def test_eligibility_count_and_audited_selection():
    event, actor, track, projects = setup_case()
    award = Award.objects.create(event=event, name="Best", winner_count=1, eligibility_track=track)
    with pytest.raises(ValidationError, match="finalized submission"):
        select_winner(award=award, project=projects[0], actor=actor)
    stage = Stage.objects.create(event=event, name="Final")
    Submission.objects.create(
        project=projects[0], stage=stage, status="finalized", updated_by=actor
    )
    winner = select_winner(award=award, project=projects[0], actor=actor)
    assert winner.source == "manual"
    assert AuditEvent.objects.filter(action="award.winner_selected").count() == 1
    assert DomainEvent.objects.get(event_type="award.winner_selected").payload["event"] == str(
        event.public_id
    )
    with pytest.raises(ValidationError, match="already won"):
        select_winner(award=award, project=projects[0], actor=actor)
    Submission.objects.create(
        project=projects[1], stage=stage, status="finalized", updated_by=actor
    )
    with pytest.raises(ValidationError, match="count"):
        select_winner(award=award, project=projects[1], actor=actor)


def test_stacking_and_conflict_group_fail_closed():
    event, actor, _, projects = setup_case()
    first = Award.objects.create(
        event=event, name="First", require_finalized_submission=False, allow_stacking=False
    )
    second = Award.objects.create(event=event, name="Second", require_finalized_submission=False)
    select_winner(award=first, project=projects[0], actor=actor)
    with pytest.raises(ValidationError, match="stacking"):
        select_winner(award=second, project=projects[0], actor=actor)
    group_a = Award.objects.create(
        event=event, name="A", require_finalized_submission=False, conflict_group="sponsor"
    )
    group_b = Award.objects.create(
        event=event, name="B", require_finalized_submission=False, conflict_group="sponsor"
    )
    select_winner(award=group_a, project=projects[1], actor=actor)
    with pytest.raises(ValidationError, match="conflict"):
        select_winner(award=group_b, project=projects[1], actor=actor)
    assert AwardWinner.objects.count() == 2


def test_cross_event_project_cannot_win():
    event, actor, _, projects = setup_case()
    other = Event.objects.create(workspace=event.workspace, name="Other", slug="other")
    award = Award.objects.create(event=other, name="Other", require_finalized_submission=False)
    with pytest.raises(ValidationError, match="award event"):
        select_winner(award=award, project=projects[0], actor=actor)


def test_evaluation_selection_requires_published_rank_or_audited_override():
    event, actor, _, projects = setup_case()
    stage = Stage.objects.create(event=event, name="Judging")
    plan = EvaluationPlan.objects.create(stage=stage, name="Final")
    award = Award.objects.create(
        event=event,
        name="Judged",
        require_finalized_submission=False,
        selection_source="evaluation",
        evaluation_plan=plan,
    )
    with pytest.raises(ValidationError, match="published"):
        select_winner(award=award, project=projects[0], actor=actor)
    run = NormalizationRun.objects.create(
        plan=plan,
        number=1,
        ridge_lambda=1.0,
        iterations=1,
        converged=True,
        grand_mean=3.0,
        evidence={
            "projects": {
                str(projects[0].pk): {"raw": 5.0, "final": 5.0},
                str(projects[1].pk): {"raw": 3.0, "final": 3.0},
            }
        },
    )
    plan.published_normalization_run = run
    plan.save(update_fields=["published_normalization_run"])
    with pytest.raises(ValidationError, match="override reason"):
        select_winner(award=award, project=projects[1], actor=actor)
    winner = select_winner(
        award=award,
        project=projects[1],
        actor=actor,
        override_reason="Documented eligibility exception",
    )
    assert winner.evidence["rank"] == 2
    assert winner.override_reason == "Documented eligibility exception"
    assert (
        AuditEvent.objects.get(action="award.winner_selected").metadata["override_reason"]
        == winner.override_reason
    )


def test_track_award_ranks_its_eligible_field_not_the_whole_event():
    event, actor, track, projects = setup_case()
    other_track = Track.objects.create(event=event, name="Other")
    rival = Project.objects.create(event=event, created_by=actor, name="Rival", track=other_track)
    stage = Stage.objects.create(event=event, name="Judging")
    plan = EvaluationPlan.objects.create(stage=stage, name="Final")
    scores = {rival: 9.0, projects[0]: 5.0, projects[1]: 4.0, projects[2]: 3.0}
    run = NormalizationRun.objects.create(
        plan=plan,
        number=1,
        ridge_lambda=1.0,
        iterations=1,
        converged=True,
        grand_mean=5.0,
        evidence={"projects": {str(p.pk): {"raw": s, "final": s} for p, s in scores.items()}},
    )
    plan.published_normalization_run = run
    plan.save(update_fields=["published_normalization_run"])
    award = Award.objects.create(
        event=event,
        name="Best in track",
        require_finalized_submission=False,
        selection_source="evaluation",
        evaluation_plan=plan,
        eligibility_track=track,
    )
    winner = select_winner(award=award, project=projects[0], actor=actor)
    assert winner.evidence["rank"] == 1 and winner.override_reason == ""
    with pytest.raises(ValidationError, match="outside the award's eligible track"):
        select_winner(award=award, project=rival, actor=actor)
    other = Award.objects.create(
        event=event,
        name="Second",
        require_finalized_submission=False,
        selection_source="evaluation",
        evaluation_plan=plan,
        eligibility_track=track,
    )
    with pytest.raises(ValidationError, match="override reason"):
        select_winner(award=other, project=projects[1], actor=actor)
