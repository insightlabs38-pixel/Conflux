"""Deterministic, explainable baseline assignment (JDG-007), extended with a
connectivity-aware objective for the assigned-subset strategy (JDG-009/010).

Track-fit prefers a judge whose PoolMembership.track_expertise includes the
candidate Project's `track` (added as a corrective fix ahead of C-B15 --
Project previously had no Track association at all, silently degrading
this to a permanent tie; see DECISIONS.md).
"""

from dataclasses import dataclass

from .connectivity import connectivity_report, repair_connectivity
from .eligibility import eligible_projects
from .models import Assignment, ConflictOfInterest, EvaluationPoolStrategy, PoolMembership


@dataclass(frozen=True)
class Pairing:
    judge_id: int
    project_id: int


@dataclass(frozen=True)
class RebalanceCalculation:
    pairs: list[Pairing]
    current_pairs: list[Pairing]
    candidate_ids: list[int]
    coverage: int


def track_fit(judge_track_ids: set[int], project_track_id: int | None) -> int:
    """1 if the judge's declared expertise covers the candidate's track, else 0."""
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

    candidates = list(eligible_projects(plan).order_by("id"))
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
        eligible.sort(key=lambda j: (-track_fit(judge_tracks[j], project_track_id), load[j], j))
        for judge_id in eligible[: min(coverage, len(eligible))]:
            load[judge_id] += 1
            pairs.append(Pairing(judge_id, project.id))

    # Connectivity-aware objective (JDG-010): the pure coverage/load pass
    # above can leave the judge-overlap graph disconnected (e.g. coverage=1
    # never creates any overlap at all). Stitch it back together where
    # feasible -- see connectivity.repair_connectivity for the bound.
    # One candidate has no cross-project ranking to calibrate; keep its
    # coverage/track-fit choice instead of assigning extra judges for overlap.
    if len(judge_ids) > 1 and len(candidates) > 1:
        pairs, _ = repair_connectivity(pairs, judge_ids=judge_ids, load=load, conflicts=conflicts)
    return pairs


def build_evidence(plan, pairs: list[Pairing], *, coverage: int, solver: str = "heuristic") -> dict:
    per_judge = {}
    for pairing in pairs:
        per_judge[pairing.judge_id] = per_judge.get(pairing.judge_id, 0) + 1
    conflict_count = ConflictOfInterest.objects.filter(event_id=plan.stage.event_id).count()
    return {
        "solver": solver,
        "coverage": coverage,
        "candidate_count": len({p.project_id for p in pairs}),
        "judge_count": len(per_judge),
        "assignment_count": len(pairs),
        "load_by_judge": {str(k): v for k, v in sorted(per_judge.items())},
        "conflict_count": conflict_count,
        "connectivity": connectivity_report(pairs, per_judge.keys()).as_dict(),
    }


def preview(plan, *, coverage: int = 3) -> dict:
    """Read-only preview of what `activate(plan, coverage=coverage)` would
    produce -- the same coverage/load/conflict/expertise(-via-connectivity)
    evidence, without writing an AssignmentVersion or touching `plan`'s
    active one (S04). Lets an organizer compare several coverage values
    before committing to an activation, which is otherwise immutable once
    created.
    """
    pairs = compute_assignment(plan, coverage=coverage)
    return build_evidence(plan, pairs, coverage=coverage)


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
    version = AssignmentVersion.objects.create(
        plan=plan,
        number=next_number,
        coverage=coverage,
        evidence=build_evidence(plan, pairs, coverage=coverage),
    )
    Assignment.objects.bulk_create(
        [Assignment(version=version, judge_id=p.judge_id, project_id=p.project_id) for p in pairs]
    )
    plan.active_assignment_version = version
    plan.save(update_fields=["active_assignment_version", "updated_at"])
    return version


def compute_rebalance(
    plan, *, drop_judge_ids: set[int] | None = None, coverage: int | None = None
) -> RebalanceCalculation:
    """Compute the same pairings a rebalance would freeze, without writing."""
    from .models import Ballot

    if plan.pool_strategy != EvaluationPoolStrategy.ASSIGNED_SUBSET:
        raise ValueError("Rebalancing only applies to the assigned-subset strategy.")
    current = plan.active_assignment_version
    if current is None:
        raise ValueError("This plan has no active assignment to rebalance.")

    drop_judge_ids = set(drop_judge_ids or ())
    coverage = current.coverage if coverage is None else coverage

    submitted = set(
        Ballot.objects.filter(rubric_version__plan=plan, is_calibration=False).values_list(
            "judge_id", "project_id"
        )
    )
    current_pairs = [Pairing(a.judge_id, a.project_id) for a in current.assignments.all()]

    memberships = list(
        PoolMembership.objects.filter(pool_id=plan.pool_id)
        .prefetch_related("track_expertise")
        .order_by("judge_id")
    )
    judge_tracks = {m.judge_id: {t.id for t in m.track_expertise.all()} for m in memberships}
    active_judge_ids = [m.judge_id for m in memberships if m.judge_id not in drop_judge_ids]
    conflicts = set(
        ConflictOfInterest.objects.filter(event_id=plan.stage.event_id).values_list(
            "judge_id", "project_id"
        )
    )
    candidates = list(eligible_projects(plan).order_by("id"))

    load = dict.fromkeys(active_judge_ids, 0)
    kept_pairs: list[Pairing] = []
    kept_by_project: dict[int, set[int]] = {}
    for pairing in current_pairs:
        key = (pairing.judge_id, pairing.project_id)
        if pairing.judge_id in drop_judge_ids and key not in submitted:
            continue  # pending work for a dropped judge -- reassigned below
        kept_pairs.append(pairing)
        kept_by_project.setdefault(pairing.project_id, set()).add(pairing.judge_id)
        if pairing.judge_id in load:
            load[pairing.judge_id] += 1

    new_pairs = list(kept_pairs)
    for project in candidates:
        already = kept_by_project.get(project.id, set())
        needed = coverage - len(already)
        if needed <= 0:
            continue
        project_track_id = getattr(project, "track_id", None)
        eligible = [
            j for j in active_judge_ids if j not in already and (j, project.id) not in conflicts
        ]
        eligible.sort(
            key=lambda j: (-track_fit(judge_tracks.get(j, set()), project_track_id), load[j], j)
        )
        for judge_id in eligible[:needed]:
            load[judge_id] += 1
            new_pairs.append(Pairing(judge_id, project.id))

    if len(active_judge_ids) > 1 and len(candidates) > 1:
        new_pairs, _ = repair_connectivity(
            new_pairs, judge_ids=active_judge_ids, load=load, conflicts=conflicts
        )

    return RebalanceCalculation(
        pairs=new_pairs,
        current_pairs=current_pairs,
        candidate_ids=[project.id for project in candidates],
        coverage=coverage,
    )


def rebalance(plan, *, drop_judge_ids: set[int] | None = None, coverage: int | None = None):
    """Freeze a new assignment after judge dropout, preserving submitted work."""
    from .models import AssignmentVersion

    calculation = compute_rebalance(plan, drop_judge_ids=drop_judge_ids, coverage=coverage)
    drop_judge_ids = set(drop_judge_ids or ())
    next_number = (
        plan.assignment_versions.order_by("-number").values_list("number", flat=True).first() or 0
    ) + 1
    evidence = build_evidence(plan, calculation.pairs, coverage=calculation.coverage)
    evidence["rebalanced_from"] = plan.active_assignment_version.number
    evidence["dropped_judges"] = sorted(drop_judge_ids)
    version = AssignmentVersion.objects.create(
        plan=plan, number=next_number, coverage=calculation.coverage, evidence=evidence
    )
    Assignment.objects.bulk_create(
        [
            Assignment(version=version, judge_id=p.judge_id, project_id=p.project_id)
            for p in calculation.pairs
        ]
    )
    plan.active_assignment_version = version
    plan.save(update_fields=["active_assignment_version", "updated_at"])
    return version


def simulate_dropout(plan, *, drop_judge_ids: set[int]) -> dict:
    """Summarize coverage risk and replacement work using rebalance's exact solver."""
    calculation = compute_rebalance(plan, drop_judge_ids=drop_judge_ids)
    before = {(p.judge_id, p.project_id) for p in calculation.current_pairs}
    after = {(p.judge_id, p.project_id) for p in calculation.pairs}
    coverage_by_project = {project_id: 0 for project_id in calculation.candidate_ids}
    for pairing in calculation.pairs:
        if pairing.project_id in coverage_by_project:
            coverage_by_project[pairing.project_id] += 1
    return {
        "evidence": build_evidence(plan, calculation.pairs, coverage=calculation.coverage),
        "pending_removed": len(before - after),
        "assignments_added": len(after - before),
        "coverage_gaps": [
            {"project_id": project_id, "missing": calculation.coverage - count}
            for project_id, count in coverage_by_project.items()
            if count < calculation.coverage
        ],
    }
