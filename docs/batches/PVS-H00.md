# PVS-H00 — Baseline/release evidence snapshot
## Result
Clean baseline at the post-VS50 HEAD: official acceptance, Core tests, cold/offline Compose, restart, backup/restore and browser smoke are green. Evidence: `docs/verification/PVS-H00/`.
## Changes
- Formatted three tracked docs that failed `format:check` (VS40/VS41-era); no product change.
## Verification
- Acceptance (unmodified checker, fresh stack) → `claimed T1 T2, verified T1 T2`; migrations 84 applied/0 pending; reseed idempotent; state survives restart.
- `make verify-fast` equivalents → 1081 backend, 119+7 frontend passed; OpenAPI/SDK/block-schema fresh. Cold start 45 s; backup/restore and offline smoke PASS.
- k6 gallery+health, 10 VUs → p95 51.6 ms, 0 failures; demo generator and accessibility report run on PostgreSQL (18 pages, 0 failures); desktop/mobile screenshots, no console errors.
## Limitations
- Owner-dirty `tests/test_master_supervisor.py` (Ruff E501) and `master/worker_prompt.md` (Prettier) fail repo-wide lint/format; untouched.
- Public server-rendered pages apply no `--font-sans`/link styling (serif, default blue links): PVS-H03 finding. No Playwright suite exists yet (PVS-H03). Tier claim stays T1/T2 (no released T3/T4 checker).
## Next
PVS01.
