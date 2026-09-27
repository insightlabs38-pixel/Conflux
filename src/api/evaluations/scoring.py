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
    from .models import Ballot

    ballots = Ballot.objects.filter(rubric_version__plan=plan).prefetch_related(
        "responses", "rubric_version"
    )
    observations = []
    for ballot in ballots:
        scores = {response.criterion_id: response.score for response in ballot.responses.all()}
        criteria = [c for c in ballot.rubric_version.criteria if c["id"] in scores]
        if not criteria:
            continue
        observations.append((ballot.judge_id, ballot.project_id, weighted_score(criteria, scores)))
    return observations
