# PVS07 — Sequential implementation checkpoint

## Result

Core, Stretch, Very-Stretch (VS01–VS50), PVS-H00, PVS01–PVS05, PVS-H01, PVS06 and PVS07 complete on `main`. Earliest unfinished batch: **PVS08**, then PVS09, PVS10, PVS-H02, PVS11–PVS15, PVS-H03, PVS16–PVS18 (PVS18 only if PVS-H02 finds a bottleneck), PVS-H04, PVS-H05.

## Changes

- Each batch has `docs/batches/<ID>.md`; operator docs in `docs/operations/`; PVS-H00/H01 evidence in `docs/verification/`.
- New apps: `taxonomy`, `eligibility`, `deliberation`, `onsite`; new libs `segno`, `pyyaml`.
- Standing guards: `tests/security` (route/isolation/fuzz/CSRF/idempotency sweeps), `tests/integration/concurrency/test_pvs_races.py` (PostgreSQL), final-archive guard test that forces every new event-owned model to be archived or excluded.
- Preserve unrelated owner dirt: `.gitignore`, `master.sh`, `master/`, `tests/test_master_supervisor.py`. Never `ruff format` the `tests/` root or add those files.

## Verification

- Full suite: SQLite 1169 passed/20 skipped; PostgreSQL 17 (`DATABASE_URL=postgres://conflux:conflux@localhost:15432/conflux` from `COMPOSE_PROJECT_NAME=confluxh00 POSTGRES_PORT=15432 ... docker compose up -d db`, see `/tmp/h00-env.sh` pattern in docs/verification/PVS-H00) 1168 passed/5 skipped at PVS-H01.
- Env for tests: `DJANGO_SECRET_KEY=analytics-test-only RECORD_SIGNING_KEY_SEED=000…001 DJANGO_DEBUG=1`; run `.venv/bin/pytest tests -q -n auto -p no:logging`.
- After any API change: `manage.py spectacular --validate --fail-on-warn --file docs/api/openapi.yaml`, `scripts/generate_sdks.py`, then `scripts/check_openapi_artifact.py` and `scripts/generate_sdks.py --check`.

## Limitations

- PVS features are API/CLI only so far; UI, Playwright scenes and demo package are PVS-H03/H05. Public server-rendered pages lack font/link styling (H03 finding).
- Session tokens unhashed at rest (documented in PVS-H01 findings).

## Next

PVS08 (safe submission artifact/demo inspector), then in order. Code freeze Tuesday 2026-09-29 18:00 UTC; stop new features at 08:00 UTC that day.
