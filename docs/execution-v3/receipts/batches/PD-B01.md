# PD-B01 — Current correctness and integration repair
## Result
All 6 tasks DONE. Baseline had no P0/P1; repairable P2/P3 correctness/integration findings fixed at root cause.
## Changes
- `JudgeWorkspace`: re-selecting the current event/stage no longer strands "Loading stages…" (+ vitest regression).
- Real prior-release upgrade smoke test (`release-freeze` dump → migrate → known records) replaces a permanent skip.
- `lifecycle` e2e canary fails fast with an actionable precondition message; runbooks updated.
## Verification
- `make verify-fast` → pytest 1401 passed/23 skipped; web 169 + embed 8; format/lint/build/sdk clean
- PG17 `pytest -n auto` → 1420 passed/4 skipped; `./scripts/e2e-fast` → 144 passed/0 failed on rebuilt stack
- `make backup-restore-smoke` → PASS; S3 contract vs RustFS → 3 passed; `validate_queue.py` → valid
## Limitations
- Open non-blockers D-03/05/08/10/12/13 owned by later batches (`docs/verification/PD-B01/BLOCKER_REGISTER.md`).
- Same agent repaired and reviewed; cold/offline smoke not re-run (no infra change).
## Next
PD-B02 backend test-tail optimization. Checkpoint: `checkpoints/CP-PD-B01.yaml`.
