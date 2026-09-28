from audit.services import record_mutation
from community.models import VotingPlan
from community.results import tally
from django.core.exceptions import ValidationError
from django.db import transaction
from evaluations.results import ranked_results
from projects.models import Project, SubmissionStatus

from .models import Award, AwardWinner, FulfillmentState, PrizeFulfillment, SelectionSource


def published_awards_for_public_display(event):
    """Award name + winning project names, for unauthenticated public
    surfaces (the site's "results" page block, S19). Deliberately a
    narrower shape than the admin `_award_data` in awards.views -- no
    selection mechanics, evidence, or fulfillment state.
    """
    from presentation.models import PublicationSurface
    from presentation.publication import publication_visible

    if not publication_visible(event, PublicationSurface.WINNERS):
        return []
    return [
        {
            "public_id": str(award.public_id),
            "name": award.name,
            "winners": [
                {
                    "project_public_id": str(winner.project.public_id),
                    "project_name": winner.project.name,
                }
                for winner in award.winners.select_related("project").order_by("selected_at")
            ],
        }
        for award in Award.objects.filter(event=event, published_at__isnull=False).order_by("pk")
    ]


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
            Award.objects.select_for_update(of=("self",))
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
        package = getattr(award, "prize_package", None)
        if package:
            PrizeFulfillment.objects.bulk_create(
                [
                    PrizeFulfillment(winner=winner, component=component)
                    for component in package.components.all()
                ]
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


NEXT_STATES = {
    FulfillmentState.PENDING: FulfillmentState.CONTACTED,
    FulfillmentState.CONTACTED: FulfillmentState.VERIFIED,
    FulfillmentState.VERIFIED: FulfillmentState.SENT,
}


def advance_fulfillment(*, fulfillment, target, actor, note=""):
    with transaction.atomic():
        fulfillment = (
            PrizeFulfillment.objects.select_for_update(of=("self",))
            .select_related("winner__award__event", "component")
            .get(pk=fulfillment.pk)
        )
        current = fulfillment.state
        allowed = target == NEXT_STATES.get(current) or (
            current == FulfillmentState.SENT
            and target in (FulfillmentState.CLAIMED, FulfillmentState.FAILED)
        )
        if not allowed:
            raise ValidationError("Invalid fulfillment transition.")
        if target == FulfillmentState.FAILED and not note.strip():
            raise ValidationError("Failure requires a note.")
        fulfillment.state = target
        fulfillment.note = note.strip()
        fulfillment.updated_by = actor
        fulfillment.save(update_fields=["state", "note", "updated_by", "updated_at"])
        award = fulfillment.winner.award
        record_mutation(
            actor=actor,
            workspace=award.event.workspace,
            action="prize.fulfillment_advanced",
            target=fulfillment,
            metadata={"state": target, "note": fulfillment.note},
            event_type="prize.fulfillment_advanced",
            payload={
                "event": str(award.event.public_id),
                "award": str(award.public_id),
                "state": target,
            },
        )
        return fulfillment
