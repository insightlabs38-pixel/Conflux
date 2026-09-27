"""VS01: an explicit optimization-grade assignment solver, additive to and
independent from the deterministic greedy heuristic in `assignment.py`
(never replaces it -- see `compare` below and `views.AssignmentCompareView`).

Models judge/project coverage assignment as a min-cost flow:

  source -> judge -> project -> sink

- A hard conflict is enforced structurally: no judge->project edge exists
  for a conflicted pair, so the solver can never produce one (not a
  post-hoc check).
- Coverage is a hard flow constraint: each project's edge to the sink has
  capacity exactly `coverage` (or fewer if too few eligible judges exist).
- Load is balanced by splitting each judge's source edge into `unit
  capacity` parallel edges with strictly increasing marginal cost
  (0, 1, 2, ...); a successive-shortest-path solver always fills the
  cheapest edges first, so it fills a judge's 1st slot before their 2nd,
  the 2nd before the 3rd, and so on across every judge -- the standard
  technique for minimizing a convex (here: sum-of-squares-like) function
  of load through a linear-cost flow solver.
- Expertise is a soft cost: a track-fit match costs 0, a mismatch costs
  `TRACK_MISMATCH_COST`, so the solver prefers a fit whenever it doesn't
  cost more load imbalance than that.
- Connectivity is not a flow objective (it isn't linear/convex in the
  same sense) -- exactly like the heuristic, the flow's raw output is run
  through the same `repair_connectivity` pass, so the two solvers are
  compared on equal footing for that dimension rather than one being
  penalized for skipping a step the other gets for free.

No optimization library is added: for a hackathon's judge/project scale
(tens, not thousands), a pure-Python successive-shortest-augmenting-path
solver (Bellman-Ford/SPFA per augmentation, since parallel-edge costs
make Dijkstra-with-potentials more bookkeeping than the scale justifies)
finds the exact optimum for this objective in well under a second.
"""

from collections import deque
from dataclasses import dataclass

from .assignment import Pairing, build_evidence, track_fit
from .coi import conflict_pairs
from .connectivity import repair_connectivity
from .eligibility import eligible_projects
from .expertise import judge_track_ids_for_pool
from .models import EvaluationPoolStrategy, PoolMembership

TRACK_MISMATCH_COST = 1


@dataclass
class _Edge:
    to: int
    cap: int
    cost: int
    rev: int  # index of the reverse edge in graph[to]


class MinCostFlow:
    """A textbook successive-shortest-augmenting-path min-cost flow solver
    over a residual graph with parallel edges. Every cost here is
    non-negative by construction (0, `TRACK_MISMATCH_COST`, or a
    load-staircase index), so SPFA never has to contend with a negative
    cycle -- the one situation this style of solver cannot handle.
    """

    def __init__(self, node_count: int):
        self.graph: list[list[_Edge]] = [[] for _ in range(node_count)]

    def add_edge(self, frm: int, to: int, cap: int, cost: int) -> None:
        self.graph[frm].append(_Edge(to, cap, cost, len(self.graph[to])))
        self.graph[to].append(_Edge(frm, 0, -cost, len(self.graph[frm]) - 1))

    def solve(self, source: int, sink: int, max_flow: int) -> tuple[int, int]:
        """Push up to `max_flow` units from `source` to `sink` along
        successively more expensive shortest paths until either that
        target is reached or no augmenting path remains (some demand is
        infeasible, e.g. too few uncoflicted judges for a project's full
        coverage -- the same graceful shortfall the heuristic allows).
        Returns (flow actually sent, its total cost).
        """
        flow = 0
        cost = 0
        n = len(self.graph)
        while flow < max_flow:
            dist = [None] * n
            dist[source] = 0
            in_queue = [False] * n
            prev_node: list[int | None] = [None] * n
            prev_edge: list[int | None] = [None] * n
            queue = deque([source])
            in_queue[source] = True
            while queue:
                u = queue.popleft()
                in_queue[u] = False
                for i, edge in enumerate(self.graph[u]):
                    if edge.cap <= 0:
                        continue
                    candidate_dist = dist[u] + edge.cost
                    if dist[edge.to] is None or candidate_dist < dist[edge.to]:
                        dist[edge.to] = candidate_dist
                        prev_node[edge.to] = u
                        prev_edge[edge.to] = i
                        if not in_queue[edge.to]:
                            queue.append(edge.to)
                            in_queue[edge.to] = True
            if dist[sink] is None:
                break
            push = max_flow - flow
            v = sink
            while v != source:
                u = prev_node[v]
                push = min(push, self.graph[u][prev_edge[v]].cap)
                v = u
            v = sink
            while v != source:
                u = prev_node[v]
                edge = self.graph[u][prev_edge[v]]
                edge.cap -= push
                self.graph[v][edge.rev].cap += push
                v = u
            flow += push
            cost += push * dist[sink]
        return flow, cost


def compute_assignment_optimized(plan, *, coverage: int = 3) -> list[Pairing]:
    """Pure function, no DB writes -- the optimized counterpart to
    `assignment.compute_assignment`. Only meaningful for the
    assigned-subset strategy: under all-judges every eligible judge
    already reviews every candidate, so there is no assignment choice
    left to optimize.
    """
    if plan.pool_id is None:
        raise ValueError("This plan has no evaluation pool to assign from.")
    if plan.pool_strategy != EvaluationPoolStrategy.ASSIGNED_SUBSET:
        raise ValueError("The optimization solver only applies to the assigned-subset strategy.")

    memberships = list(
        PoolMembership.objects.filter(pool_id=plan.pool_id)
        .prefetch_related("track_expertise")
        .order_by("judge_id")
    )
    judge_tracks = judge_track_ids_for_pool(memberships, plan.stage.event)
    judge_ids = [m.judge_id for m in memberships]
    candidates = list(eligible_projects(plan).order_by("id"))
    conflicts = conflict_pairs(
        plan.stage.event_id,
        judge_ids=set(judge_ids),
        project_ids={project.id for project in candidates},
    )
    if not judge_ids or not candidates:
        return []

    # Node layout: 0 = source, judges, projects, sink.
    judge_node = {judge_id: 1 + i for i, judge_id in enumerate(judge_ids)}
    project_node = {project.id: 1 + len(judge_ids) + i for i, project in enumerate(candidates)}
    sink = 1 + len(judge_ids) + len(candidates)
    solver = MinCostFlow(sink + 1)

    for judge_id in judge_ids:
        node = judge_node[judge_id]
        # One unit-capacity edge per possible marginal assignment, cost
        # increasing by 1 each time -- the convex-cost-via-parallel-edges
        # trick: SPFA always drains the cheapest (least-loaded) edge
        # first, so this judge's load only rises past k once every judge
        # with load < k has already been offered that same cheap slot.
        for marginal in range(len(candidates)):
            solver.add_edge(0, node, 1, marginal)

    edge_projects: list[tuple[int, int]] = []  # (judge_id, project_id) per judge->project edge
    for project in candidates:
        p_node = project_node[project.id]
        project_track_id = getattr(project, "track_id", None)
        for judge_id in judge_ids:
            if (judge_id, project.id) in conflicts:
                continue
            fit = track_fit(judge_tracks[judge_id], project_track_id)
            solver.add_edge(
                judge_node[judge_id],
                p_node,
                1,
                0 if fit else TRACK_MISMATCH_COST,
            )
            edge_projects.append((judge_id, project.id))
        solver.add_edge(p_node, sink, coverage, 0)

    target = coverage * len(candidates)
    solver.solve(0, sink, target)

    pairs: list[Pairing] = []
    for judge_id, project_id in edge_projects:
        node = judge_node[judge_id]
        p_node = project_node[project_id]
        for edge in solver.graph[node]:
            if edge.to == p_node and edge.cap == 0:
                pairs.append(Pairing(judge_id, project_id))
                break

    load = dict.fromkeys(judge_ids, 0)
    for pairing in pairs:
        load[pairing.judge_id] += 1
    if len(judge_ids) > 1 and len(candidates) > 1:
        pairs, _ = repair_connectivity(pairs, judge_ids=judge_ids, load=load, conflicts=conflicts)
    return pairs


def compare(plan, *, coverage: int = 3) -> dict:
    """Side-by-side evidence for the existing heuristic and this
    optimized solver against the same plan/coverage, so an organizer can
    see the actual tradeoff rather than trusting either blindly.
    """
    from .assignment import compute_assignment

    heuristic_pairs = compute_assignment(plan, coverage=coverage)
    optimized_pairs = compute_assignment_optimized(plan, coverage=coverage)
    return {
        "heuristic": build_evidence(plan, heuristic_pairs, coverage=coverage),
        "optimized": build_evidence(plan, optimized_pairs, coverage=coverage, solver="optimized"),
    }


def activate_optimized(plan, *, coverage: int = 3):
    """Compute + freeze a new AssignmentVersion from this solver, and make
    it `plan`'s active one -- the optimized counterpart to
    `assignment.activate`, sharing the exact same AssignmentVersion/
    Assignment models (only `evidence["solver"]` distinguishes which
    solver produced a given version). Caller wraps this in a transaction
    and records an audit event, same as `activate`.
    """
    from .models import Assignment, AssignmentVersion

    pairs = compute_assignment_optimized(plan, coverage=coverage)
    next_number = (
        plan.assignment_versions.order_by("-number").values_list("number", flat=True).first() or 0
    ) + 1
    version = AssignmentVersion.objects.create(
        plan=plan,
        number=next_number,
        coverage=coverage,
        evidence=build_evidence(plan, pairs, coverage=coverage, solver="optimized"),
    )
    Assignment.objects.bulk_create(
        [Assignment(version=version, judge_id=p.judge_id, project_id=p.project_id) for p in pairs]
    )
    plan.active_assignment_version = version
    plan.save(update_fields=["active_assignment_version", "updated_at"])
    return version
