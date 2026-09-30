# PD-B03 — new E2E architecture vs the baseline suite

Baseline: `e1888de` (UIV2-B10), measured in PD-B00 (`docs/verification/PD-B00/BASELINE_RESULTS.md`): `demo-reset` (12 s) + `e2e-fast`, 144 passed / 91 skipped / 0 failed, **3 m 48 s**; serial `make demo-e2e` not run (≈ 8 min estimated).

## 1. Coverage is a superset

`npx playwright test --list` on `e1888de`'s `tests/e2e` vs now (both projects, test ids without line numbers):

|                          |                                                                                                                                       ids |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------: |
| baseline                 |                                                                                                                                       235 |
| now                      |                                                                                                                                       289 |
| in baseline, missing now |                                                                                                                                     **0** |
| new                      | 54 = `auth-states` 10 + `fixture-isolation` 6 + `release-integrity` 8 + `pdv3-baseline-census` 30 (opt-in, skipped unless `E2E_CENSUS=1`) |

Executed tiered run (`scripts/e2e-tiers`, generated table in `COVERAGE.md`): **156 passed (132 desktop + 24 mobile), 103 skipped by design, 0 failed** = the 144 baseline passes + 12 from the three new specs (their 24 ids: 12 desktop passes and 12 mobile skips; 91 + 12 = 103 skips). Every baseline journey still runs on the same unmodified assertions. Three specs received root-cause robustness fixes, not relaxations: `uiv2-gate` waits for the SPA before pressing Tab; `lifecycle` addresses the finalist table by region instead of ambiguous text; `workspace-shell`'s new-tab check asserts the link contract deterministically and retries only the popup plumbing (logs `T07-gate-race-fix.log`, `T11-workspace-shell-popup-*.log`).

## 2. Stronger than the baseline

- Mutating specs no longer share or consume seed 7 (per-file `iso-min` fixtures); a cross-fixture isolation spec and probe prove mutations and sessions do not leak (`fixture-isolation`, `probe_isolation.py`, 403 cross-access).
- The lifecycle canary gained `release-integrity`: API-level cross-stage checks that fail on a never-run lifecycle and on a ballot deleted behind the API (`T09-integrity-gate-detects-breakage.log`), plus the authoritative serial run kept and its ordering defect fixed (`lifecycle` used to run after `uiv2-organizer`).
- Two latent load-dependent test races found and fixed; the suite now has a measured reliability budget and flake report (`make e2e-report`).
- Sharding is collision-safe and verified by running two shards concurrently on one stack.

## 3. Materially lower feedback latency

| Loop                    | Baseline                        | Now                                              |
| ----------------------- | ------------------------------- | ------------------------------------------------ |
| Smoke                   | none (full suite only)          | 11 s (16 tests)                                  |
| Affected change         | none                            | 35–49 s (one mapped spec)                        |
| PR / full (single host) | 3 m 48 s + 12 s reset           | 2 m 22 s median, no reset (−38%)                 |
| Mutating-spec re-run    | needs `demo-reset` first        | none: fixtures are created per run (4–9 s)       |
| Release                 | unmeasured serial (~8 min est.) | 9.0 min serial measured + canary gate ~2 min/run |

## 4. Repeatability

21 full tiered runs recorded (`logs/T10-history.jsonl`): 20 clean, 1 failed (`workspace-shell` popup loss, run 11, diagnostic re-run passed, reported as flaky and then fixed at the root); **10/10 consecutive clean runs after the fix** (median 142 s, max 143 s; `T11-report-post-fix.log`). Canary repeat gate 2/2. Popup stress 96/96 ×3 passing (before: 5–7 failures per 48).

## 5. Isolation/parallel regression cases (all pass)

Backend `tests/integration/test_e2e_fixtures.py` (10) and `tests/test_e2e_tiers.py` (39); PostgreSQL 17 full suite 1472 passed / 4 skipped (`T11-pytest-postgres.log`); concurrent shards 1/2 + 2/2 on one stack (92 + 60 = 152 passed at the time, equal to unsharded).
