# PVS04 — Physical judge route optimization
## Result
Judges and organizers get deterministic, distance-minimizing walking orders over exactly the projects each judge is already expected to evaluate.
## Changes
- `onsite.routing` (exact Held-Karp up to 9 stops, greedy+2-opt beyond) and route endpoints; candidate rule extracted to `evaluations.candidates` so judging and routing cannot diverge.
## Verification
- `test_judge_routes.py` → 7 passed (brute-force optimality, determinism, distance model, conflicts/ineligible/unplaced exclusion, assigned-subset scope, authz, foreign start location); evaluation suites unchanged (142 passed).
## Limitations
- Single-judge routes only (no crowd staggering); coordinates are organizer-entered.
- Footage unaffected: no public surface changes.
## Next
PVS05.
