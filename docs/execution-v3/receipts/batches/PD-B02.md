# PD-B02 — Backend test-tail optimization
## Result
All 6 tasks DONE. Backend suite 78 s → 22 s (SQLite) and 97 s → 44 s (PostgreSQL 17) with no coverage removed.
## Changes
- Test-only fast password hasher (`tests/conftest.py`; hashing was ~73% of CPU) + 3 fidelity guards for the production hasher.
- `make test` uses `--dist worksteal`; fixed `test_route_sweep` leaking committed rows (flaked `test_demo_scenarios`); added conftest leak detector.
- `CONTRIBUTING.md` backend feedback targets; before/after in `docs/verification/PD-B02/RESULTS.md`.
## Verification
- `make verify-fast` → pytest 1404 passed/23 skipped (22 s); web 169 + embed 8; format/lint/build/sdk clean
- PG17 `pytest -n auto --dist worksteal` → 1423 passed/4 skipped, 5/5 clean runs (43–46 s)
- collected ids vs e1888de → 0 tests removed; leak detector negative case fails as designed
## Limitations
- Per-worker migration setup (~7 s) left; template reuse deferred. Same agent implemented and reviewed.
## Next
PD-B03 frontend E2E isolation. Checkpoint: `checkpoints/CP-PD-B02.yaml`.
