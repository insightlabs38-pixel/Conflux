# PD-B00 — Current-state baseline and defect census
## Result
All 8 tasks DONE. Baseline `e1888de` measured from evidence; no P0/P1; 14 findings routed to PD-B01–B04.
## Changes
- `docs/verification/PD-B00/`: freeze, results, defect register, receipt, 81-capture UI census, raw logs.
- Fixed PD-R00 regression (prettier on v3 bundle); README/verification docs corrected; opt-in census spec.
## Verification
- `uv run --frozen pytest -n auto` → 1400 passed/23 skipped; PostgreSQL 17 → 1418 passed/5 skipped
- `make format-check lint sdk-check block-schema-check i18n-check build; pnpm test` → pass (168 web + 8 embed)
- `./scripts/e2e-fast` → 144 passed, 91 mobile skips, 0 failed
- `loadtests/h02/run.sh` @2/@4 workers → 147.6/222.7 req/s, 0 5xx, 8/8 integrity checks
- `python scripts/pdv3/validate_queue.py` → valid, 0 errors
## Limitations
- S3 contract, k6 scenarios, webhook/API load not run; single load run per config; same agent implemented and reviewed.
## Next
PD-B01 triage. Checkpoint: `checkpoints/CP-PD-B00.yaml`.
