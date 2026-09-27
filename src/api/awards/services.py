from audit.services import record_mutation
from community.models import VotingPlan
from community.results import tally
from django.core.exceptions import ValidationError
from django.db import transaction
from evaluations.results import ranked_results
from projects.models import Project, SubmissionStatus

from .models import Award, AwardWinner, SelectionSource


def _source_evidence(award, project):
    if award.selection_source == SelectionSource.MANUAL:
        return {}, True
    if award.selection_source == SelectionSource.EVALUATION:
        plan = award.evaluation_plan
        if plan is None or plan.published_normalization_run_id is None:
            raise ValidationError("Evaluation results must be published before winner selection.")
        rows = ranked_results(plan, plan.published_normalization_run)
        rank = next((row.rank for row in rows if row.project_id == project.pk), None)
        return {
            "plan": str(plan.public_id),
            "normalization_run": str(plan.published_normalization_run.public_id),
            "rank": rank,
        }, rank is not None and rank <= award.winner_count
    plan = VotingPlan.objects.filter(event=award.event).first()
    if plan is None or plan.results_published_at is None or not plan.has_closed():
        raise ValidationError(
            "Community results must be closed and published before winner selection."
        )
    rows = tally(plan)
    rank = next(
        (index + 1 for index, row in enumerate(rows) if row["project_id"] == project.pk), None
    )
    return {
        "voting_plan": str(plan.public_id),
        "rank": rank,
    }, rank is not None and rank <= award.winner_count


def select_winner(*, award, project, actor, override_reason=""):
    reason = override_reason.strip()
    with transaction.atomic():
        project = Project.objects.select_for_update().get(pk=project.pk)
        award = (
            Award.objects.select_for_update()
            .select_related("event", "eligibility_track", "evaluation_plan")
            .get(pk=award.pk)
        )
        if award.published_at:
            raise ValidationError("Published awards cannot be changed.")
        if project.event_id != award.event_id:
            raise ValidationError("Project must belong to the award event.")
        if award.eligibility_track_id and project.track_id != award.eligibility_track_id:
            raise ValidationError("Project is outside the award's eligible track.")
        if (
            award.require_finalized_submission
            and not project.submissions.filter(status=SubmissionStatus.FINALIZED).exists()
        ):
            raise ValidationError("Project needs a finalized submission.")
        if AwardWinner.objects.filter(award=award, project=project).exists():
            raise ValidationError("Project has already won this award.")
        if award.winners.count() >= award.winner_count:
            raise ValidationError("Winner count has been reached.")
        other_wins = AwardWinner.objects.select_related("award").filter(
            project=project, award__event=award.event
        )
        if other_wins.exists() and (
            not award.allow_stacking or other_wins.filter(award__allow_stacking=False).exists()
        ):
            raise ValidationError("Award stacking is not allowed for this project.")
        if (
            award.conflict_group
            and other_wins.filter(award__conflict_group=award.conflict_group).exists()
        ):
            raise ValidationError("Project already won in this conflict group.")
        evidence, matches_source = _source_evidence(award, project)
        if not matches_source and not reason:
            raise ValidationError(
                "Selection outside the source ranking requires an override reason."
            )
        winner = AwardWinner.objects.create(
            award=award,
            project=project,
            selected_by=actor,
            source=award.selection_source,
            evidence=evidence,
            override_reason=reason,
        )
        record_mutation(
            actor=actor,
            workspace=award.event.workspace,
            action="award.winner_selected",
            target=winner,
            metadata={
                "award": str(award.public_id),
                "project": str(project.public_id),
                "override_reason": reason,
            },
            event_type="award.winner_selected",
            payload={
                "event": str(award.event.public_id),
                "award": str(award.public_id),
                "project": str(project.public_id),
            },
        )
        return winner
