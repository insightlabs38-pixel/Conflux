# PD-B00 Baseline Freeze (T01)

Captured 2026-09-30T05:06:06Z on `main`. Product code under `src tests scripts` is unchanged since the last product commit.

## Frozen identity

- Product baseline: `e1888de8764cd1c99e7af242e8ca6d46994e33bc` (UIV2-B10, 2026-09-29 05:43 UTC). Commits after it are execution-control/docs only (`5680dcd..b5f398d`).
- Tooling: Python 3.12.3, Node v24.21.0, pnpm 12.6.0, Docker 29.8.1, uv (frozen lock), Playwright 1.63.0, `psql` client present.
- Runtime found: compose project `conflux` (app/beat/worker/caddy/db/objectstore/cache) up 23-30h, Caddy on :8080 returns 200 at `/app/`; db on :5432. Leftover stacks from earlier campaigns: `confluxh00-db-1` (:15432, up 45h) and `confluxrel33-*` (up 2d). `conflux-api:latest` image built ~23h ago (~UIV2-B10 time); exact image-to-SHA match **not verified**.

## Supported commands (Makefile / scripts)

| Purpose             | Command                                                                                                                                                                |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fast gate           | `make verify-fast` (format-check, lint, `pytest -n auto` + web/embed vitest, build, sdk-check, block-schema-check)                                                     |
| Backend / web tests | `uv run --frozen pytest -n auto`; `pnpm test`                                                                                                                          |
| Contract checks     | `make openapi-check sdk-check block-schema-check`; `make i18n-check`                                                                                                   |
| Stack               | `make up` (clean build/boot), `make dev`, `make down`, `make seed`                                                                                                     |
| Demo data           | `make demo-reset` (`scripts/demo-reset [submitted\|judged\|published]`, password `demo-pass-7`)                                                                        |
| Browser             | `make demo-e2e` / `make e2e-fast` (Playwright, needs demo-reset stack)                                                                                                 |
| Release smokes      | `make cold-boot-smoke backup-restore-smoke oidc-smoke acceptance verify-dogfood-extended`; `scripts/verify-chaos`, `scripts/verify-artifact-portability`, `loadtests/` |
| Restore frozen data | `scripts/restore demo/release-freeze` (disposable stacks only; SHA-256 in its MANIFEST.md)                                                                             |

## Documented claims to measure (not assumed true) — README/docs

- Fast gate: 1373 backend passed / 23 skipped; 137 web + 8 embed tests; format/lint/build/OpenAPI/SDK clean.
- Official acceptance checker: T1/T2 7/7 (`acceptance-report.txt`); T3/T4 manual, backed by `make verify-dogfood-extended`.
- Prior release receipts: Dex OIDC 18/18; cold/offline startup, backup/restore, chaos, artifact portability pass; load 149.6 req/s, zero 5xx/race violations (`docs/verification/PVS-H06/report.md`).
- Current PostgreSQL/Playwright: `docs/verification/final-pass/report.md`.

## Known limitations already documented (`docs/verification/README.md#remaining-limits`)

Sybil resistance is bounded; records are signed claims (no certificate designer); hosted-OIDC refresh/logout untested; deliberation notes and technical operator features API/CLI-first; artifact picker needs project re-open after upload; archives/Event-as-Code have narrower scopes; normalization assumes additive judge bias.

## Representative demo data

- Deterministic demo: `demo-hackathon-7` (24 teams/participants, 6 judges, mentor, volunteer, sponsor; checkpoints submitted/judged/published) via `scripts/demo-reset`.
- Frozen rehearsal snapshot `demo/release-freeze` (2026-09-27): event `f73490c0-f2d8-40bd-b058-d0a883fa9243`, project `a68c4383-...`, award `7e951ed4-...`.
- Official synthetic fixture `fixtures/fixtures.json`.

## Handling rules for the rest of PD-B00

Reuse the running `conflux` stack (one approved stack); do not start duplicate app stacks. Measure, do not modify product behavior. Leftover `confluxh00`/`confluxrel33` stacks are not touched (record only).
