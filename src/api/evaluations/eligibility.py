from awards.models import Award, SelectionSource
from projects.models import Project, SubmissionStatus


def eligible_projects(plan):
    candidates = Project.objects.filter(event_id=plan.stage.event_id, submissions__stage=plan.stage)
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
