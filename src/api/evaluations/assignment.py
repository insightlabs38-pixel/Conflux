"""Deterministic, explainable baseline assignment (JDG-007).

Track-fit is scored but never currently discriminates: nothing upstream
(Project/Team) records which Track a candidate belongs to, so every
judge/candidate pair ties on that factor today. Coverage (judges per
candidate) and load (assignments per judge) still balance correctly on
their own -- see the C-B14 batch report for the honest limitation.
"""

from dataclasses import dataclass

from projects.models import Project

from .models import Assignment, ConflictOfInterest, EvaluationPoolStrategy, PoolMembership


@dataclass(frozen=True)
class Pairing:
    judge_id: int
    project_id: int


def _track_fit(judge_track_ids: set[int], project_track_id: int | None) -> int:
    """1 if the judge's declared expertise covers the candidate's track, else
    0. Always 0 today: no candidate has a track_id (see module docstring).
    """
    return 1 if project_track_id is not None and project_track_id in judge_track_ids else 0


def compute_assignment(plan, *, coverage: int = 3) -> list[Pairing]:
    """Pure function: no DB writes. Returns the pairing a fresh
    AssignmentVersion should be created from.
    """
    if plan.pool_id is None:
        raise ValueError("This plan has no evaluation pool to assign from.")

    memberships = list(
        PoolMembership.objects.filter(pool_id=plan.pool_id)
        .prefetch_related("track_expertise")
        .order_by("judge_id")
    )
    judge_tracks = {m.judge_id: {t.id for t in m.track_expertise.all()} for m in memberships}
    judge_ids = [m.judge_id for m in memberships]

    candidates = list(
        Project.objects.filter(event_id=plan.stage.event_id, submissions__stage=plan.stage)
        .distinct()
        .order_by("id")
    )
    conflicts = set(
        ConflictOfInterest.objects.filter(event_id=plan.stage.event_id).values_list(
            "judge_id", "project_id"
        )
    )

    if not judge_ids or not candidates:
        return []

    if plan.pool_strategy == EvaluationPoolStrategy.ALL_JUDGES:
        return [
            Pairing(judge_id, project.id)
            for project in candidates
            for judge_id in judge_ids
            if (judge_id, project.id) not in conflicts
        ]

    # ASSIGNED_SUBSET: greedy, deterministic. For each candidate (in a fixed
    # order), pick the `coverage` eligible judges with the lowest current
    # load, preferring track-fit, tie-broken by judge id -- so re-running
    # against the same inputs always reproduces the same assignment.
    load = dict.fromkeys(judge_ids, 0)
    pairs: list[Pairing] = []
    for project in candidates:
        project_track_id = getattr(project, "track_id", None)
        eligible = [j for j in judge_ids if (j, project.id) not in conflicts]
        eligible.sort(key=lambda j: (-_track_fit(judge_tracks[j], project_track_id), load[j], j))
        for judge_id in eligible[: min(coverage, len(eligible))]:
            load[judge_id] += 1
            pairs.append(Pairing(judge_id, project.id))
    return pairs


def activate(plan, *, coverage: int = 3):
    """Compute + freeze a new AssignmentVersion, and make it `plan`'s active
    one. Caller is responsible for wrapping this in a transaction and
    recording an audit event (see evaluations.views.AssignmentActivateView).
    """
    from .models import AssignmentVersion

    pairs = compute_assignment(plan, coverage=coverage)
    next_number = (
        plan.assignment_versions.order_by("-number").values_list("number", flat=True).first() or 0
    ) + 1
    per_judge = {}
    for pairing in pairs:
        per_judge[pairing.judge_id] = per_judge.get(pairing.judge_id, 0) + 1
    version = AssignmentVersion.objects.create(
        plan=plan,
        number=next_number,
        coverage=coverage,
        evidence={
            "candidate_count": len({p.project_id for p in pairs}),
            "judge_count": len(per_judge),
            "assignment_count": len(pairs),
            "load_by_judge": {str(k): v for k, v in sorted(per_judge.items())},
        },
    )
    Assignment.objects.bulk_create(
        [Assignment(version=version, judge_id=p.judge_id, project_id=p.project_id) for p in pairs]
    )
    plan.active_assignment_version = version
    plan.save(update_fields=["active_assignment_version", "updated_at"])
    return version
