# PVS-H04 — Release verification (HEAD 16e43ba plus this commit)

Every gate below was run against this tree; stack gates used a cold Compose project built from it (empty volumes).

| Gate                                            | Command / method                                                                                      | Result                                                                                                |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Official acceptance                             | vendored checker vs cold stack, freshly seeded (`acceptance-report.txt`)                              | 7/7 PASS, claimed T1 T2, verified T1 T2                                                               |
| Tier/bonus claims                               | `.dogfood.toml` + README                                                                              | unchanged: T1/T2 only; no unreleased-tier claims                                                      |
| Backend tests                                   | SQLite `pytest -n auto` / PostgreSQL 17 `pytest -n 4`                                                 | 1337 passed, 23 skipped / 1355 passed, 5 skipped                                                      |
| Security/isolation                              | `tests/security` route/IDOR/CSRF/fuzz sweeps (auto-cover new routes) + per-batch cross-scope tests    | pass; read-only sweep over every event-scoped write route                                             |
| Concurrency/deadlines                           | PostgreSQL race suites (PVS03/05/01/02/11) + H02 same-resource races                                  | pass, 70/70 races single-winner                                                                       |
| Load/performance                                | `loadtests/h02/run.sh`, 4 workers, 156 actors, 60 s                                                   | 184 req/s, 0 5xx, all DB↔response reconciliations PASS (`load-workers4.json`)                         |
| Browser journeys + a11y                         | Playwright, desktop + mobile, axe WCAG 2 A/AA                                                         | 32/32 pass                                                                                            |
| Lint/format/types/build                         | ruff format+check, prettier, tsc (web, embed), `manage.py check`, vite/SDK builds, block-schema check | clean (only the owner's untracked `tests/test_master_supervisor.py` / `master/` are outside the gate) |
| API contract                                    | `spectacular --fail-on-warn`, `check_openapi_artifact`, `generate_sdks --check`                       | clean                                                                                                 |
| Cold Compose start                              | `down -v` → `up --build --wait`                                                                       | healthy in 19 s (cached layers)                                                                       |
| Offline start                                   | `scripts/cold-offline-smoke` (internal network)                                                       | PASS                                                                                                  |
| Restart persistence                             | `docker compose restart`, data re-read                                                                | PASS                                                                                                  |
| Backup/restore                                  | `scripts/backup-restore-smoke`                                                                        | PASS                                                                                                  |
| Migrations/upgrade                              | older release DB (51 migrations) dumped, migrated to HEAD; `makemigrations --check`                   | applied cleanly; workspace/project/audit counts identical; no drift                                   |
| Chaos / artifact portability                    | `verify-chaos`, `verify-artifact-portability`                                                         | 35 + 3 passed / PASS (RustFS↔SeaweedFS)                                                               |
| Webhooks, import/export, archive reconstruction | `test_webhooks*`, `test_archive*`, `test_final_archive` (incl. PVS tables)                            | pass                                                                                                  |
| Live spot checks (real ASGI stack)              | MCP tools/list+call, cookie refused, read-only 503 + Retry-After, ICS, badge                          | as designed                                                                                           |
| Docs                                            | README (web app now served at `/app/`), `docs/operations/*` per feature                               | synchronized                                                                                          |

## Defects found and fixed during PVS-H02..H04

Unbounded DB connections under bursts (500s) · IP-keyed vote throttle locking a whole venue · newer exception grant hidden by an expired one · web app never served by Compose · no sign-in form · unstyled public pages · spurious voting-results 404 · `select_for_update` outer-join hazard in continuation moderation (caught by the standing guard).

## Known limitations

PVS01–PVS17 have no dedicated UI panels (API, API explorer, MCP); session tokens are unhashed at rest (H01 finding); gallery endpoint is unpaginated; SSO not exercised against a real provider (fake provider tests only).
