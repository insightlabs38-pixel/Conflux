"""Judge-project overlap/connectivity metrics and repair (JDG-009/010/011).

Cross-judge score normalization (C-B16) is only meaningful if the
judge-overlap graph -- an edge between two judges whenever they share at
least one assigned candidate -- is connected: that's the only way a
transitive chain of comparisons can calibrate every judge's scale against
every other's. This module measures that graph's health and (for the
assigned-subset strategy only) deterministically repairs full
disconnection; it never claims to eliminate every weak bridge, only to
report them.
"""

from dataclasses import dataclass


def overlap_graph(pairs) -> dict[int, set[int]]:
    """judge_id -> set of judge_ids sharing at least one candidate with it."""
    judges_by_project: dict[int, set[int]] = {}
    for pairing in pairs:
        judges_by_project.setdefault(pairing.project_id, set()).add(pairing.judge_id)
    adjacency: dict[int, set[int]] = {}
    for judges in judges_by_project.values():
        for judge_id in judges:
            adjacency.setdefault(judge_id, set())
        for a in judges:
            for b in judges:
                if a != b:
                    adjacency[a].add(b)
    return adjacency


def connected_components(adjacency: dict[int, set[int]], judge_ids) -> list[set[int]]:
    seen: set[int] = set()
    components = []
    for start in sorted(judge_ids):
        if start in seen:
            continue
        stack = [start]
        component: set[int] = set()
        while stack:
            node = stack.pop()
            if node in component:
                continue
            component.add(node)
            stack.extend(adjacency.get(node, set()) - component)
        seen |= component
        components.append(component)
    return components


def cut_vertices(adjacency: dict[int, set[int]], judge_ids) -> list[int]:
    """Judges whose removal increases the component count -- a weak bridge
    in the overlap graph. Brute force (remove one node, recount components);
    judge/pool sizes here are small enough that this is plenty fast and,
    unlike a from-scratch Tarjan implementation, is obviously correct.
    """
    judge_ids = list(judge_ids)
    baseline = len(connected_components(adjacency, judge_ids))
    cuts = []
    for candidate in judge_ids:
        remaining = [j for j in judge_ids if j != candidate]
        trimmed = {
            j: {n for n in neighbors if n != candidate}
            for j, neighbors in adjacency.items()
            if j != candidate
        }
        if len(connected_components(trimmed, remaining)) > baseline and len(remaining) > 0:
            cuts.append(candidate)
    return sorted(cuts)


@dataclass(frozen=True)
class ConnectivityReport:
    connected: bool
    component_count: int
    component_sizes: list[int]
    isolated_judges: int
    cut_judges: list[int]

    def as_dict(self) -> dict:
        return {
            "connected": self.connected,
            "component_count": self.component_count,
            "component_sizes": self.component_sizes,
            "isolated_judges": self.isolated_judges,
            "cut_judges": self.cut_judges,
        }


def connectivity_report(pairs, judge_ids) -> ConnectivityReport:
    judge_ids = list(judge_ids)
    if not judge_ids:
        return ConnectivityReport(True, 0, [], 0, [])
    adjacency = overlap_graph(pairs)
    components = connected_components(adjacency, judge_ids)
    isolated = sum(1 for j in judge_ids if not adjacency.get(j))
    cuts = cut_vertices(adjacency, judge_ids) if len(components) == 1 else []
    return ConnectivityReport(
        connected=len(components) <= 1,
        component_count=len(components),
        component_sizes=sorted((len(c) for c in components), reverse=True),
        isolated_judges=isolated,
        cut_judges=cuts,
    )


def repair_connectivity(pairs, *, judge_ids, load, conflicts, max_extra_per_judge=2):
    """Deterministically add minimal extra (judge, project) pairs so the
    overlap graph has one component, when that's feasible without exceeding
    `max_extra_per_judge` additional assignments on the bridging judge or
    violating a declared conflict. Returns (new_pairs, extra_added).

    Not always achievable (e.g. a single candidate can't link disjoint
    judges who never reviewed it and can't take on a conflicting one) --
    `connectivity_report` on the result is the authoritative honesty check,
    not this function's return value.
    """
    judge_ids = list(judge_ids)
    pairs = list(pairs)
    pairing_cls = type(pairs[0]) if pairs else None
    extra_added = 0
    repairs_by_judge: dict[int, int] = {}
    projects_by_judge: dict[int, set[int]] = {}
    for pairing in pairs:
        projects_by_judge.setdefault(pairing.judge_id, set()).add(pairing.project_id)

    for _ in range(len(judge_ids)):  # bounded: components only ever merge
        adjacency = overlap_graph(pairs)
        components = connected_components(adjacency, judge_ids)
        if len(components) <= 1 or pairing_cls is None:
            break
        components.sort(key=lambda c: (len(c), min(c)))
        bridge = None
        for index, first in enumerate(components):
            for second in components[index + 1 :]:
                for source, target in ((first, second), (second, first)):
                    for judge_a in sorted(source, key=lambda j: (load.get(j, 0), j)):
                        if repairs_by_judge.get(judge_a, 0) >= max_extra_per_judge:
                            continue
                        for judge_b in sorted(target, key=lambda j: (load.get(j, 0), j)):
                            candidate_projects = sorted(
                                p
                                for p in projects_by_judge.get(judge_b, set())
                                - projects_by_judge.get(judge_a, set())
                                if (judge_a, p) not in conflicts
                            )
                            if candidate_projects:
                                bridge = (judge_a, candidate_projects[0])
                                break
                        if bridge:
                            break
                    if bridge:
                        break
                if bridge:
                    break
            if bridge:
                break
        if bridge is None:
            break
        judge_a, project_id = bridge
        pairs.append(pairing_cls(judge_id=judge_a, project_id=project_id))
        projects_by_judge.setdefault(judge_a, set()).add(project_id)
        load[judge_a] = load.get(judge_a, 0) + 1
        repairs_by_judge[judge_a] = repairs_by_judge.get(judge_a, 0) + 1
        extra_added += 1
    return pairs, extra_added
