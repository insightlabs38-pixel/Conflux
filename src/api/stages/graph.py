"""Whole-graph validation and deterministic ordering (ST-002).

StageTransition.clean() (ST-001) rejects a cycle at the moment one edge is
added, but that only holds for code paths that actually call .clean() —
`bulk_create`, which a bulk graph-replace endpoint (ST-005) would reasonably
want to use, skips model validation entirely. These functions re-check the
whole graph from the database, so a bulk write can't silently produce an
invalid graph just because it bypassed the per-instance guard.
"""

from collections import defaultdict

from django.core.exceptions import ValidationError

from .models import Stage, StageTransition


class StageGraphError(ValidationError):
    pass


def _edges_for(event):
    return list(
        StageTransition.objects.filter(from_stage__event=event).values_list(
            "from_stage_id", "to_stage_id"
        )
    )


def topological_order(event):
    """Deterministic topological order of `event`'s stages (Kahn's
    algorithm). Ties are broken by (position, id), never by dict/set
    iteration order, so the same graph always orders the same way.
    Raises StageGraphError if the graph has a cycle.
    """
    stages = list(Stage.objects.filter(event=event))
    by_id = {s.pk: s for s in stages}
    indegree = dict.fromkeys(by_id, 0)
    adjacency = defaultdict(list)
    for src, dst in _edges_for(event):
        adjacency[src].append(dst)
        indegree[dst] += 1

    def sort_key(stage_id):
        stage = by_id[stage_id]
        return (stage.position, stage.pk)

    ready = sorted((sid for sid, deg in indegree.items() if deg == 0), key=sort_key)
    ordered = []
    while ready:
        current = ready.pop(0)
        ordered.append(by_id[current])
        newly_ready = []
        for neighbor in adjacency[current]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                newly_ready.append(neighbor)
        ready = sorted(ready + newly_ready, key=sort_key)

    if len(ordered) != len(stages):
        raise StageGraphError("Stage graph contains a cycle.")
    return ordered


def validate_event_graph(event):
    """Whole-graph invariants, re-derived from the database rather than
    trusted from however the edges got written:
      - no cycle (direct or indirect)
      - no stage transitions to itself
      - at least one initial stage
      - every stage is reachable from some initial stage (no orphans)
    """
    stages = list(Stage.objects.filter(event=event))
    if not stages:
        return

    edges = _edges_for(event)
    for src, dst in edges:
        if src == dst:
            raise StageGraphError("A stage cannot transition to itself.")

    topological_order(event)  # raises StageGraphError on a cycle

    initial_ids = {s.pk for s in stages if s.is_initial}
    if not initial_ids:
        raise StageGraphError("An event's stage graph needs at least one initial stage.")

    adjacency = defaultdict(list)
    for src, dst in edges:
        adjacency[src].append(dst)

    reachable = set(initial_ids)
    frontier = list(initial_ids)
    while frontier:
        current = frontier.pop()
        for neighbor in adjacency[current]:
            if neighbor not in reachable:
                reachable.add(neighbor)
                frontier.append(neighbor)

    orphans = sorted(s.name for s in stages if s.pk not in reachable)
    if orphans:
        raise StageGraphError(f"Stage(s) unreachable from any initial stage: {', '.join(orphans)}.")
