# PVS-H06 — release closure report

Run against the working tree that became the final commit; the Compose stack was rebuilt from it.

## What changed

| Area           | Result                                                                                                                                                                                                                                                                                                                                       |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Session tokens | `accounts.Session` stores a keyed SHA-256 digest (`token_digest`); the raw token exists only in the cookie. Migration `0005` digests existing rows in place (tested, and applied to the long-running dev stack DB). Tests assert the presented token appears in no stored column, a stored digest is not a valid credential, logout revokes. |
| Gallery        | `limit` (1–100, default 50) / `offset`, `X-Total-Count`, `Link` on both JSON endpoints (bodies stay bare arrays, so the official checker, SDKs and embed keep working); server-rendered page paginates at 24 with filters preserved; embed has "Load more". 15 new tests incl. constant query count.                                         |
| PVS UI         | Panels in the existing organizer/judge/participant workspaces plus a mentor/volunteer desk; map in `docs/operations/PVS_UI.md`. 12 new component tests, 2 new Playwright specs.                                                                                                                                                              |
| OIDC           | Real-provider smoke against Dex (18/18, `oidc-dex-smoke.txt`) in addition to the local test provider. Hosted providers not tested.                                                                                                                                                                                                           |
| Demo reset     | `scripts/demo-reset` with a checkpoint argument (`submitted`, `judged` or `published`), default `submitted` (open event, unjudged, unpublished, two live participants). Event/workspace public IDs derived from the seed; e2e addresses people by username.                                                                                  |
| Control plane  | `master.sh`, `master/`, supervisor tests and `.gitignore` committed; lint and Prettier fixed; 4 supervisor tests pass.                                                                                                                                                                                                                       |

## Defects found and fixed while testing the product

- Creating a demo checkpoint before close crashed `demo_showcase` (continuation requires a closed event).
- Organizer dashboard overflowed horizontally (up to 1578 px wide at 390 px): a long `<select>` inside a shrink-to-fit label.
- Permission explorer had an unnamed `<select>` (axe `select-name`).
- Public event page probed voting results that are always 403 until published (console error); status now says `results_published`, the client skips the probe.
- Awards panel went stale after finalizing in the deliberation room.
- Load harness `seed.py` created sessions by raw token (updated to digests).

## Evidence

| Gate                                                                | Result                                                                                                                                                                                        |
| ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Official acceptance (`make acceptance`)                             | claimed T1 T2, verified T1 T2; all 7 checks PASS                                                                                                                                              |
| `make verify-fast` (format, lint, tests, build, SDK/schema)         | 1366 passed / 23 skipped (SQLite) + 137 web tests + 8 embed tests; all checks clean                                                                                                           |
| PostgreSQL 17, full suite                                           | 1384 passed / 5 skipped                                                                                                                                                                       |
| Blank-DB cold `docker compose up --build --wait` (isolated project) | boots, migrates through `0005`, seeds, serves paginated gallery                                                                                                                               |
| Existing-DB upgrade                                                 | dev stack DB (46 h old) migrated in place by the rebuilt image                                                                                                                                |
| Offline boot (`cold-offline-smoke`, no egress)                      | PASS (start from a stopped stack)                                                                                                                                                             |
| Backup/restore smoke; chaos; artifact portability                   | PASS; PASS; PASS                                                                                                                                                                              |
| Load (frozen `loadtests/h02`), saturated 2 workers, 60 s            | 149.6 req/s (baseline 141.9), 0 5xx, 0 race violations, all integrity checks PASS; some organizer-endpoint p95s vary with fewer samples (progress, vote-results) — throughput did not regress |
| Load, unsaturated 4 workers, 45 s                                   | 77.6 req/s (76.6), 0 5xx, all integrity PASS, p95s equal or lower                                                                                                                             |
| Playwright                                                          | submitted checkpoint: 61 tests (50 pass, 11 desktop-only skipped on mobile); published checkpoint: 37 pass; per-role PVS axe/overflow 10 pass                                                 |
| Real-provider OIDC (Dex)                                            | 18/18                                                                                                                                                                                         |

## Remaining, non-blocking

- Hosted OIDC providers, refresh tokens and logout propagation are untested/unsupported.
- Judge deliberation stances/notes are API-only (no judge-facing room discovery); technical PVS features stay CLI/API-first.
- Playwright workflow specs consume demo state and need a fresh `scripts/demo-reset` per run.
- `cold-offline-smoke` must start from a stopped stack.
- Existing web tests use generic fetch mocks, so new panels render their error notice there (logged, not failing); the new panel tests cover real payloads.
- Saturated-load p95s move ±15% run to run on this host.
