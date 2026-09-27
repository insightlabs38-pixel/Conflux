"""Read-only award allocation proposals using the winner selection constraints."""

from community.models import VotingPlan
from community.results import tally
from evaluations.results import ranked_results
from projects.models import Project, SubmissionStatus

from .models import Award, AwardWinner, SelectionSource


def _ranked_candidates(award, projects):
    if award.selection_source == SelectionSource.MANUAL:
        return list(projects), None
    if award.selection_source == SelectionSource.EVALUATION:
        plan = award.evaluation_plan
        if plan is None or plan.published_normalization_run_id is None:
            return [], "Publish evaluation results before requesting proposals."
        ranked = ranked_results(plan, plan.published_normalization_run)
        ids = [row.project_id for row in ranked if row.rank <= award.winner_count]
    else:
        plan = VotingPlan.objects.filter(event=award.event).first()
        if plan is None or plan.results_published_at is None or not plan.has_closed():
            return [], "Close and publish community results before requesting proposals."
        ids = [row["project_id"] for row in tally(plan)[: award.winner_count]]
    by_id = {project.id: project for project in projects}
    return [by_id[project_id] for project_id in ids if project_id in by_id], None


def propose_allocations(event, *, max_nodes=50000):
    awards = list(
        Award.objects.filter(event=event)
        .select_related("evaluation_plan__published_normalization_run")
        .order_by("id")
    )
    projects = list(Project.objects.filter(event=event).order_by("name", "public_id"))
    finalized = set(
        Project.objects.filter(
            event=event, submissions__status=SubmissionStatus.FINALIZED
        ).values_list("id", flat=True)
    )
    winners = list(
        AwardWinner.objects.filter(award__event=event).select_related("award", "project")
    )
    existing = {award.id: [] for award in awards}
    used = {}
    for winner in winners:
        existing[winner.award_id].append(winner.project_id)
        used.setdefault(winner.project_id, []).append(winner.award)

    rows = []
    for award in awards:
        candidates = [
            project
            for project in projects
            if (
                award.eligibility_track_id is None or project.track_id == award.eligibility_track_id
            )
            and (not award.require_finalized_submission or project.id in finalized)
            and project.id not in existing[award.id]
        ]
        ranked, blocker = _ranked_candidates(award, candidates)
        rows.append(
            {
                "award": award,
                "existing": existing[award.id],
                "candidates": ranked if not award.published_at else [],
                "slots_needed": max(award.winner_count - len(existing[award.id]), 0),
                "capacity": max(award.winner_count - len(existing[award.id]), 0)
                if not award.published_at and blocker is None
                else 0,
                "blocker": blocker,
            }
        )

    search_rows = sorted(rows, key=lambda row: (len(row["candidates"]), row["award"].id))
    best = {award.id: [] for award in awards}
    chosen = {award.id: [] for award in awards}
    best_count = -1
    best_cost = float("inf")
    nodes = 0
    search_limited = False

    def compatible(award, project_id):
        for prior in used.get(project_id, ()):
            if not award.allow_stacking or not prior.allow_stacking:
                return False
            if award.conflict_group and award.conflict_group == prior.conflict_group:
                return False
        return True

    def search(row_index, start, slots, count, cost):
        nonlocal best, best_count, best_cost, nodes, search_limited
        if nodes >= max_nodes:
            search_limited = True
            return
        nodes += 1
        if row_index == len(search_rows):
            if count > best_count or (count == best_count and cost < best_cost):
                best_count, best_cost = count, cost
                best = {award_id: list(ids) for award_id, ids in chosen.items()}
            return
        row = search_rows[row_index]
        award = row["award"]
        if slots == 0:
            search(
                row_index + 1,
                0,
                search_rows[row_index + 1]["capacity"] if row_index + 1 < len(search_rows) else 0,
                count,
                cost,
            )
            return
        candidates = row["candidates"]
        for index in range(start, len(candidates)):
            project = candidates[index]
            if not compatible(award, project.id):
                continue
            chosen[award.id].append(project.id)
            used.setdefault(project.id, []).append(award)
            search(row_index, index + 1, slots - 1, count + 1, cost + index)
            used[project.id].pop()
            if not used[project.id]:
                del used[project.id]
            chosen[award.id].pop()
        search(
            row_index + 1,
            0,
            search_rows[row_index + 1]["capacity"] if row_index + 1 < len(search_rows) else 0,
            count,
            cost,
        )

    search(0, 0, search_rows[0]["capacity"] if search_rows else 0, 0, 0)
    by_id = {project.id: project for project in projects}
    return {
        "search_limited": search_limited,
        "awards": [
            {
                "award": str(row["award"].public_id),
                "name": row["award"].name,
                "existing": [str(by_id[project_id].public_id) for project_id in row["existing"]],
                "proposed": [
                    str(by_id[project_id].public_id) for project_id in best[row["award"].id]
                ],
                "unfilled": row["slots_needed"] - len(best[row["award"].id]),
                "blocker": row["blocker"],
            }
            for row in rows
        ],
    }
