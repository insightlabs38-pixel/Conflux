from awards.models import Award, SelectionSource
from projects.models import Project, SubmissionStatus


def eligible_projects(plan):
    candidates = Project.objects.filter(event_id=plan.stage.event_id, submissions__stage=plan.stage)
    if plan.hybrid_source_id:
        # VS03: a pairwise plan with a rubric hybrid_source is bounded to
        # that source's own close calls, not the whole field -- see
        # evaluations.hybrid.close_call_project_ids. No published run yet
        # means nothing is bounded yet, not "everything is eligible".
        from .hybrid import close_call_project_ids

        source = plan.hybrid_source
        latest_run = source.normalization_runs.order_by("-number").first()
        if latest_run is None:
            return candidates.none()
        candidates = candidates.filter(id__in=close_call_project_ids(source, latest_run))
    if plan.prize_judging:
        awards = list(
            Award.objects.filter(evaluation_plan=plan, selection_source=SelectionSource.EVALUATION)[
                :2
            ]
        )
        if len(awards) != 1:
            return candidates.none()
        award = awards[0]
        if award.eligibility_track_id:
            candidates = candidates.filter(track_id=award.eligibility_track_id)
        if award.require_finalized_submission:
            candidates = candidates.filter(submissions__status=SubmissionStatus.FINALIZED)
    return candidates.distinct()
