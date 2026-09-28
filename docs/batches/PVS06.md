# PVS06 — Deterministic judging replay
## Result
Any published run can be replayed from its frozen ballots and cross-checked against live evidence, with tamper, deletion and omission detection.
## Changes
- `evaluations.replay` (rubric and pairwise), `GET .../runs/<run>/replay/` with optional ranking timeline; digests make reports comparable.
## Verification
- `test_judging_replay.py` → 7 passed (exact/deterministic replay, timeline, altered ballot/result/grand mean, deleted and omitted ballots, authz/scope, pairwise).
## Limitations
- Pairwise replay relies on live comparisons (evidence keeps outputs only).
- Footage unaffected: no public surface changes.
## Next
PVS07.
