"""Portable judging audit capsule (PVS07): everything needed to re-check a
published rubric result without this server. Judges are pseudonymous (J01..)
and projects carry stable labels (P01..); the signed envelope is the archive
signer's (`integrations.signed_archive`), and `scripts/verify_capsule.py`
re-checks it offline.
"""

from awards.models import Award, AwardWinner
from eligibility.models import EligibilityReview
from integrations.signed_archive import sign_archive
from projects.models import Project

from . import replay
from .models import EvaluationMode
from .results import ranked_results

CAPSULE_VERSION = 1
KIND = "judging-audit-capsule"


class CapsuleUnavailable(Exception):
    pass


def build_capsule(plan):
    run = plan.published_normalization_run
    if plan.mode != EvaluationMode.RUBRIC or run is None:
        raise CapsuleUnavailable("Only published rubric results have an audit capsule.")
    evidence = run.evidence
    ballots = evidence.get("ballots", [])
    projects = {
        p.pk: p
        for p in Project.objects.filter(pk__in={int(k) for k in evidence.get("projects", {})})
    }
    project_label = {pk: f"P{i + 1:02d}" for i, pk in enumerate(sorted(projects))}
    judge_ids = sorted({b["judge_id"] for b in ballots})
    judge_label = {pk: f"J{i + 1:02d}" for i, pk in enumerate(judge_ids)}
    results = ranked_results(plan, run)
    report = replay.replay_normalization(plan, run)
    awards = []
    for award in Award.objects.filter(evaluation_plan=plan).order_by("name", "pk"):
        winners = AwardWinner.objects.filter(award=award).select_related("project")
        awards.append(
            {
                "name": award.name,
                "winner_count": award.winner_count,
                "published": award.published_at is not None,
                "winners": [
                    {
                        "project": project_label.get(w.project_id, w.project.name),
                        "source": w.source,
                        "override_reason": w.override_reason,
                        "evidence": w.evidence,
                    }
                    for w in winners
                ],
            }
        )
    rulings = [
        {"project": project_label[r.project_id], "status": r.status, "note": r.decision_note}
        for r in EligibilityReview.objects.filter(
            project_id__in=list(projects), status__in=["ineligible", "cleared"]
        ).order_by("project_id")
    ]
    capsule = {
        "capsule_version": CAPSULE_VERSION,
        "kind": KIND,
        "event": {
            "public_id": str(plan.stage.event.public_id),
            "name": plan.stage.event.name,
        },
        "plan": {
            "name": plan.name,
            "stage": plan.stage.name,
            "rubric_versions": [
                {"public_id": str(v.public_id), "number": v.number, "criteria": v.criteria}
                for v in plan.rubric_versions.order_by("number")
            ],
            "tie_breaks": {
                project_label[int(k)]: v
                for k, v in (plan.tie_breaks or {}).items()
                if int(k) in project_label
            },
        },
        "projects": [
            {
                "label": project_label[pk],
                "public_id": str(projects[pk].public_id),
                "name": projects[pk].name,
            }
            for pk in sorted(projects)
        ],  # fmt: skip
        "run": {
            "public_id": str(run.public_id),
            "number": run.number,
            "ridge_lambda": run.ridge_lambda,
            "iterations": run.iterations,
            "converged": run.converged,
            "grand_mean": run.grand_mean,
            "created_at": run.created_at.isoformat(),
            "judge_effects": {
                judge_label[int(k)]: v
                for k, v in sorted(
                    evidence.get("judge_effects", {}).items(), key=lambda kv: int(kv[0])
                )
                if int(k) in judge_label
            },
        },
        "ballots": [
            {
                "ballot": b["ballot"],
                "judge": judge_label[b["judge_id"]],
                "project": project_label[b["project_id"]],
                "responses": b["responses"],
                "weighted_score": b["weighted_score"],
                "adjusted_score": b.get("adjusted_score"),
                "submitted_at": b["submitted_at"],
            }
            for b in ballots
        ],
        "results": [
            {
                "rank": r.rank,
                "project": project_label[r.project_id],
                "raw": r.raw_score,
                "final": r.final_score,
                "tie_break": r.tie_break,
            }
            for r in results
        ],
        "awards": awards,
        "eligibility_rulings": rulings,
        "replay": {
            "verdict": report["verdict"],
            "algorithm": report["algorithm"],
            "inputs_digest": report["inputs"]["digest"],
            "report_digest": report["report_digest"],
        },
    }
    return sign_archive(capsule)
