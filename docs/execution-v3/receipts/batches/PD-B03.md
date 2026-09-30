# PD-B03 — Frontend E2E isolation and fast-feedback architecture
## Result
All 11 tasks DONE. PR browser loop 3m48s+reset → 2m22s with no reset; smoke 11 s; affected 35–49 s; lifecycle canary and serial gate kept and strengthened.
## Changes
- `manage.py e2e_fixture` + `fixtures.ts`: throwaway per-spec/per-shard scenarios on reserved seeds, storage states by role, persistent-stack preflight (`e2e-stack`).
- `scripts/e2e-tiers`: read-only / isolated-mutation / canary tiers, smoke, affected, weighted collision-safe sharding, canary gate with `release-integrity`, run history + flake report.
- Failure-first capture (trace re-run on failure, media only with `E2E_CAPTURE=visual`); two load races and a serial-order defect fixed at the root.
## Verification
- 10/10 consecutive `make e2e-fast` after final fix → 156 passed/103 skipped/0 failed, median 142 s; 21 recorded runs, 1 flake fixed
- `make demo-reset demo-e2e` (serial, after last change) → 156 passed/0 failed, 9.0 min; `make e2e-canary REPEAT=2` → 2/2
- `make verify-fast` → pytest 1453/23 skipped, web 169 + embed 8; PG17 `pytest -n auto` → 1472 passed/4 skipped
- Baseline 235 test ids: 0 missing (`docs/verification/PD-B03/EQUIVALENCE.md`); `validate_queue.py` → valid
## Limitations
- One 8-core host: sharded speedup across machines and a scheduled CI workflow not exercised (recipe in `docs/operations/E2E.md`).
- New-tab check may need a 2nd popup attempt under heavy load (12/96 at 8 workers, annotated); same agent implemented and reviewed.
## Next
PD-B04 routing/server-state foundation. Checkpoint: `checkpoints/CP-PD-B03.yaml`.
