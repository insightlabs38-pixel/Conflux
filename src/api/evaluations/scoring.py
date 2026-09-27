"""Bridges real Ballot data into the generic (judge_id, project_id, score)
observations the normalization estimator takes (NORM-002).

Each ballot's aggregate score always uses its OWN rubric_version's frozen
criteria weights (weighted_score), never the plan's current draft or
latest published weights: a ballot cast under an earlier rubric version
must keep meaning exactly what it meant when it was cast. This is the "no
accidental weight re-estimation" guarantee -- the aggregation weights are
whatever the rubric said at submission time, never numerically refit from
the score data itself.
"""

from .rubric import weighted_score


def ballot_observations(plan):
    """[(judge_id, project_id, weighted_score), ...] for every ballot ever
    cast under any of `plan`'s rubric versions.
    """
    observations, _ = scored_ballots(plan)
    return observations


def scored_ballots(plan):
    """Return observations and a frozen authored-score trace from one ballot query."""
    from .models import Ballot

    ballots = (
        Ballot.objects.filter(rubric_version__plan=plan, is_calibration=False)
        .order_by("id")
        .select_related("rubric_version", "judge")
        .prefetch_related("responses")
    )
    observations = []
    snapshots = []
    for ballot in ballots:
        scores = {response.criterion_id: response.score for response in ballot.responses.all()}
        criteria = [c for c in ballot.rubric_version.criteria if c["id"] in scores]
        if not criteria:
            continue
        score = weighted_score(criteria, scores)
        observations.append((ballot.judge_id, ballot.project_id, score))
        snapshots.append(
            {
                "ballot": str(ballot.public_id),
                "judge": str(ballot.judge.public_id),
                "judge_id": ballot.judge_id,
                "project_id": ballot.project_id,
                "rubric_version": str(ballot.rubric_version.public_id),
                "responses": [
                    {
                        "criterion_id": criterion["id"],
                        "criterion_name": criterion["name"],
                        "weight": criterion["weight"],
                        "score": scores[criterion["id"]],
                    }
                    for criterion in criteria
                ],
                "weighted_score": score,
                "submitted_at": ballot.submitted_at.isoformat(),
            }
        )
    return observations, snapshots
