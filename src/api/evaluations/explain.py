"""Deterministic, human-readable account of why a project ranked where it did
(PVS07). Text is assembled from frozen run evidence with fixed templates: the
same run always yields the same words.
"""

from statistics import mean

from .results import ranked_results


def _ordinal(n):
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _signed(value):
    return f"{value:+.2f}"


def explain(plan, project, *, detailed):
    """`detailed` adds per-judge lines and neighbouring projects (organizers);
    the participant view stays aggregated so judges and rivals stay unidentifiable.
    """
    run = plan.published_normalization_run
    evidence = run.evidence
    results = ranked_results(plan, run)
    total = len(results)
    row = next(r for r in results if r.project_id == project.pk)
    ballots = [b for b in evidence.get("ballots", []) if b["project_id"] == project.pk]
    raw_order = sorted(
        results,
        key=lambda r: (-(r.raw_score if r.raw_score is not None else float("-inf")), r.project_id),
    )
    raw_rank = next(i + 1 for i, r in enumerate(raw_order) if r.project_id == project.pk)
    adjustment = row.final_score - (row.raw_score if row.raw_score is not None else row.final_score)

    criteria = {}
    for ballot in ballots:
        for response in ballot["responses"]:
            entry = criteria.setdefault(
                response["criterion_id"],
                {
                    "criterion": response["criterion_name"],
                    "weight": response["weight"],
                    "scores": [],
                },
            )
            entry["scores"].append(response["score"])
    criteria_rows = [
        {
            "criterion": c["criterion"],
            "weight": c["weight"],
            "mean_score": round(mean(c["scores"]), 4),
            "scores_counted": len(c["scores"]),
        }
        for _, c in sorted(criteria.items())
    ]

    sentences = [
        f"{project.name} ranked {_ordinal(row.rank)} of {total} with a final score of "
        f"{row.final_score:.2f}."
    ]
    if row.raw_score is not None:
        sentences.append(
            f"Its judges' average authored score was {row.raw_score:.2f}; removing estimated "
            f"judge scoring bias adjusted it by {_signed(adjustment)}."
        )
    if raw_rank != row.rank:
        sentences.append(f"Without that adjustment it would have ranked {_ordinal(raw_rank)}.")
    tied = [r for r in results if r.project_id != project.pk and r.final_score == row.final_score]
    if tied:
        sentences.append(
            f"Its final score tied exactly with {len(tied)} other project(s); the plan's "
            "tie-break values and then a fixed identifier order decided the order."
        )
    payload = {
        "project": str(project.public_id),
        "rank": row.rank,
        "of": total,
        "final_score": row.final_score,
        "raw_score": row.raw_score,
        "adjustment": round(adjustment, 6),
        "rank_without_adjustment": raw_rank,
        "ballots_counted": len(ballots),
        "criteria": criteria_rows,
        "run": str(run.public_id),
    }
    if detailed:
        by_rank = {r.rank: r for r in results}
        names = {}
        from projects.models import Project

        for p in Project.objects.filter(pk__in={r.project_id for r in results}):
            names[p.pk] = p.name
        neighbours = {}
        for label, rank in (("above", row.rank - 1), ("below", row.rank + 1)):
            other = by_rank.get(rank)
            if other is not None:
                gap = abs(other.final_score - row.final_score)
                neighbours[label] = {
                    "project": names.get(other.project_id, ""),
                    "final_score": other.final_score,
                    "gap": round(gap, 6),
                }
                sentences.append(
                    f"The project {label} it ({names.get(other.project_id, '?')}) is "
                    f"{gap:.2f} {'ahead' if label == 'above' else 'behind'}."
                )
        judge_ids = sorted({b["judge_id"] for b in ballots})
        label = {jid: f"Judge {i + 1}" for i, jid in enumerate(judge_ids)}
        payload["neighbours"] = neighbours
        payload["judges"] = [
            {
                "judge": label[b["judge_id"]],
                "authored_score": b["weighted_score"],
                "judge_effect": evidence.get("judge_effects", {}).get(str(b["judge_id"]), 0.0),
                "adjusted_score": b.get("adjusted_score"),
            }
            for b in sorted(ballots, key=lambda b: (b["judge_id"], b["ballot"]))
        ]
    payload["explanation"] = sentences
    return payload
