"""Deterministic replay of a published judging run (PVS06).

A run freezes its inputs (each counted ballot with its authored responses) and
its outputs. Replay feeds the frozen inputs back through the same solver and
compares every output, then cross-checks the frozen inputs against the ballots
that exist now. Nothing here writes; two replays of the same run are identical.
"""

import hashlib
import json
import math

from .models import Ballot, PairwiseComparison
from .normalization import (
    adjusted_score,
    estimate_judge_effects,
    project_final_score,
    raw_mean_score,
)
from .pairwise import estimate_strengths
from .results import _tie_broken_order
from .scoring import weighted_score

ALGORITHM = "additive-ridge-gauss-seidel/1"
PAIRWISE_ALGORITHM = "bradley-terry-map/1"
TIMELINE_POINTS = 20


def _close(a, b):
    return a == b or (
        a is not None and b is not None and math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
    )


def _digest(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def _check(name, ok, detail=""):
    return {"name": name, "ok": bool(ok), "detail": detail}


def _compare_maps(stored, replayed):
    differing = sorted(
        key for key in set(stored) | set(replayed) if not _close(stored.get(key), replayed.get(key))
    )
    return differing


def replay_normalization(plan, run, *, timeline=False):
    ballots = run.evidence.get("ballots", [])
    observations = [(b["judge_id"], b["project_id"], b["weighted_score"]) for b in ballots]
    result = estimate_judge_effects(observations, ridge_lambda=run.ridge_lambda)
    stored = run.evidence

    replayed_judges = {str(k): v for k, v in result.judge_effects.items()}
    project_ids = sorted({p for _, p, _ in observations}, key=str)
    replayed_projects = {
        str(p): {"raw": raw_mean_score(observations, p), "final": project_final_score(result, p)}
        for p in project_ids
    }
    checks = [
        _check("grand_mean", _close(run.grand_mean, result.grand_mean)),
        _check(
            "solver_trace",
            run.iterations == result.iterations and run.converged == result.converged,
            f"stored {run.iterations}/{run.converged}, "
            f"replayed {result.iterations}/{result.converged}",
        ),
    ]
    bad = _compare_maps(stored.get("judge_effects", {}), replayed_judges)
    checks.append(_check("judge_effects", not bad, f"differs for judges {bad}" if bad else ""))
    bad = sorted(
        p
        for p in set(stored.get("projects", {})) | set(replayed_projects)
        if not (
            p in stored.get("projects", {})
            and p in replayed_projects
            and _close(stored["projects"][p]["raw"], replayed_projects[p]["raw"])
            and _close(stored["projects"][p]["final"], replayed_projects[p]["final"])
        )
    )
    checks.append(_check("project_scores", not bad, f"differs for projects {bad}" if bad else ""))
    bad = [
        b["ballot"]
        for b in ballots
        if not _close(
            b.get("adjusted_score"), adjusted_score(result, b["judge_id"], b["weighted_score"])
        )
    ]
    checks.append(_check("adjusted_scores", not bad, f"differs for ballots {bad}" if bad else ""))

    live = {
        str(b.public_id): b
        for b in Ballot.objects.filter(rubric_version__plan=plan, is_calibration=False)
        .select_related("rubric_version", "judge")
        .prefetch_related("responses")
    }
    tampered, missing = [], []
    for entry in ballots:
        row = live.get(entry["ballot"])
        if row is None:
            missing.append(entry["ballot"])
            continue
        responses = {r.criterion_id: r.score for r in row.responses.all()}
        criteria = [c for c in row.rubric_version.criteria if c["id"] in responses]
        frozen = {r["criterion_id"]: r["score"] for r in entry["responses"]}
        if (
            frozen != responses
            or row.project_id != entry["project_id"]
            or row.judge_id != entry["judge_id"]
            or not criteria
            or not _close(weighted_score(criteria, responses), entry["weighted_score"])
        ):
            tampered.append(entry["ballot"])
    counted = {b["ballot"] for b in ballots}
    omitted = sorted(
        pid
        for pid, row in live.items()
        if pid not in counted and row.submitted_at <= run.created_at
    )
    checks.append(_check("ballots_exist", not missing, f"missing {missing}" if missing else ""))
    checks.append(
        _check("ballots_unchanged", not tampered, f"changed {tampered}" if tampered else "")
    )
    checks.append(
        _check("no_ballots_omitted", not omitted, f"omitted {omitted}" if omitted else "")
    )

    tie_breaks = plan.tie_breaks or {}
    order = _tie_broken_order(
        sorted(int(p) for p in replayed_projects),
        lambda p: replayed_projects[str(p)]["final"],
        tie_breaks,
    )
    from .results import ranked_results

    published = [r.project_id for r in ranked_results(plan, run)]
    checks.append(_check("ranking", order == published, f"replayed {order}, stored {published}"))

    report = {
        "mode": "rubric",
        "run": str(run.public_id),
        "number": run.number,
        "algorithm": ALGORITHM,
        "published": plan.published_normalization_run_id == run.id,
        "inputs": {
            "ballots": len(ballots),
            "ridge_lambda": run.ridge_lambda,
            "digest": _digest(
                [
                    {k: b[k] for k in ("ballot", "judge_id", "project_id", "weighted_score")}
                    for b in ballots
                ]
            ),
        },
        "checks": checks,
        "verdict": "verified" if all(c["ok"] for c in checks) else "mismatch",
    }
    if timeline:
        report["timeline"] = _timeline(plan, ballots, run, tie_breaks)
    report["report_digest"] = _digest({k: v for k, v in report.items() if k != "report_digest"})
    return report


def _timeline(plan, ballots, run, tie_breaks):
    """How the top of the ranking emerged as ballots arrived (submission order)."""
    from projects.models import Project

    names = {
        p.pk: {"project": str(p.public_id), "name": p.name}
        for p in Project.objects.filter(pk__in={b["project_id"] for b in ballots})
    }
    ordered = sorted(ballots, key=lambda b: (b["submitted_at"], b["ballot"]))
    if not ordered:
        return []
    step = max(1, math.ceil(len(ordered) / TIMELINE_POINTS))
    sizes = sorted({*range(step, len(ordered) + 1, step), len(ordered)})
    points = []
    for size in sizes:
        subset = ordered[:size]
        observations = [(b["judge_id"], b["project_id"], b["weighted_score"]) for b in subset]
        result = estimate_judge_effects(observations, ridge_lambda=run.ridge_lambda)
        projects = sorted({p for _, p, _ in observations})
        top = _tie_broken_order(projects, lambda p: project_final_score(result, p), tie_breaks)[:3]
        points.append(
            {
                "ballots": size,
                "through": subset[-1]["submitted_at"],
                "top": [
                    {**names[p], "final": round(project_final_score(result, p), 6)} for p in top
                ],
            }
        )
    return points


def replay_pairwise(plan, run):
    """Pairwise evidence keeps outputs only, so inputs are the comparisons recorded
    up to the moment the run was made.
    """
    comparisons = list(
        PairwiseComparison.objects.filter(plan=plan, submitted_at__lte=run.created_at).order_by(
            "pk"
        )
    )
    observations = []
    for c in comparisons:
        if c.winner_id is None:
            observations += [
                (c.project_a_id, c.project_b_id, 0.5),
                (c.project_b_id, c.project_a_id, 0.5),
            ]
        else:
            loser = c.project_b_id if c.winner_id == c.project_a_id else c.project_a_id
            observations.append((c.winner_id, loser, 1.0))
    result = estimate_strengths(observations, prior_games=run.prior_games)
    stored = run.evidence.get("projects", {})
    bad = sorted(
        p
        for p in set(stored) | {str(k) for k in result.strengths}
        if p not in stored
        or int(p) not in result.strengths
        or not _close(stored[p]["strength"], result.strengths[int(p)])
    )
    checks = [
        _check("strengths", not bad, f"differs for projects {bad}" if bad else ""),
        _check(
            "solver_trace",
            run.iterations == result.iterations and run.converged == result.converged,
        ),
    ]
    report = {
        "mode": "pairwise",
        "run": str(run.public_id),
        "number": run.number,
        "algorithm": PAIRWISE_ALGORITHM,
        "published": plan.published_pairwise_run_id == run.id,
        "inputs": {
            "comparisons": len(comparisons),
            "prior_games": run.prior_games,
            "digest": _digest([[a, b, w] for a, b, w in observations]),
        },
        "checks": checks,
        "verdict": "verified" if all(c["ok"] for c in checks) else "mismatch",
    }
    report["report_digest"] = _digest({k: v for k, v in report.items() if k != "report_digest"})
    return report
