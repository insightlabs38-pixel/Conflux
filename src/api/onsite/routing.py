"""Walking-order optimization for judges (PVS04). It only orders projects a
judge is already expected to evaluate: assignments, pools, conflicts and
eligibility are decided elsewhere and never changed here.
"""

import math
from itertools import combinations

ROOM_CHANGE = 15.0
SAME_ROOM = 5.0
DIFFERENT_ROOM = 30.0
EXACT_LIMIT = 9


def distance(a, b):
    if a.pk == b.pk:
        return 0.0
    if a.x is not None and b.x is not None:
        d = math.hypot(a.x - b.x, a.y - b.y)
        return d + (ROOM_CHANGE if a.parent_id != b.parent_id else 0.0)
    if a.parent_id and a.parent_id == b.parent_id:
        return SAME_ROOM
    return DIFFERENT_ROOM


def path_length(order, dist, start=None):
    total = dist(start, order[0]) if start is not None and order else 0.0
    return total + sum(dist(order[i], order[i + 1]) for i in range(len(order) - 1))


def _exact(stops, dist, start):
    """Held-Karp shortest open path; ties break by input order for determinism."""
    n = len(stops)
    best = {}
    for j in range(n):
        best[(1 << j, j)] = (dist(start, stops[j]) if start is not None else 0.0, None)
    for size in range(2, n + 1):
        for subset in combinations(range(n), size):
            mask = sum(1 << j for j in subset)
            for j in subset:
                prev_mask = mask ^ (1 << j)
                options = [
                    (best[(prev_mask, k)][0] + dist(stops[k], stops[j]), k)
                    for k in subset
                    if k != j
                ]
                best[(mask, j)] = min(options, key=lambda o: (round(o[0], 9), o[1]))
    full = (1 << n) - 1
    end = min(range(n), key=lambda j: (round(best[(full, j)][0], 9), j))
    order, mask, j = [], full, end
    while j is not None:
        order.append(j)
        prev = best[(mask, j)][1]
        mask ^= 1 << j
        j = prev
    return [stops[i] for i in reversed(order)]


def _heuristic(stops, dist, start):
    remaining = list(range(len(stops)))
    order = []
    here = start
    while remaining:
        pick = min(
            remaining,
            key=lambda i: (round(dist(here, stops[i]) if here is not None else 0.0, 9), i),
        )
        order.append(pick)
        remaining.remove(pick)
        here = stops[pick]
    route = [stops[i] for i in order]
    improved = True
    while improved:
        improved = False
        for i in range(len(route) - 1):
            for j in range(i + 1, len(route)):
                candidate = route[:i] + route[i : j + 1][::-1] + route[j + 1 :]
                if path_length(candidate, dist, start) + 1e-9 < path_length(route, dist, start):
                    route, improved = candidate, True
    return route


def optimize(stops, dist, start=None):
    """`stops` is a list of hashable stop objects in deterministic input order."""
    if len(stops) <= 1:
        return list(stops)
    if len(stops) <= EXACT_LIMIT:
        return _exact(stops, dist, start)
    return _heuristic(stops, dist, start)
