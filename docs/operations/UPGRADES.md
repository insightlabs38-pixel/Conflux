# Upgrade and compatibility discipline

What an operator can expect when moving to a newer build of Conflux, and
what stays stable across that move.

## Moving to a build with the shared primitives (PD-F002-B01)

Additive only: migrations `core/0002_saved_views`, `0003_jobs`, `0004_approvals` and `0005_threads` add tables and change nothing that exists, so they apply on the normal startup `migrate` and a rollback to the previous image simply leaves them unused. Two new Celery tasks need the **worker and beat to be restarted on the new image** (`docker compose up -d --build` rebuilds all three services; the `app` container alone does not carry them): `core.tasks.run_job` and the beat entries `sweep-jobs` (every 60 s: fails jobs that stopped reporting, re-sends queued ones that never started) and `sweep-approvals` (every 5 minutes: marks lapsed approvals). Until the worker is updated, a started job (an archive export) stays queued, and the sweep, once beat is current, re-sends it. Approval gates are off for every existing event, so no behavior changes until an organizer turns one on. See [shared primitives](../architecture/SHARED_PRIMITIVES.md).

## Application startup: normal migrations, no destructive hacks

`infra/api.Dockerfile`'s entrypoint runs, in order, every time the `app`
container starts:

```
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec uvicorn config.asgi:application ...
```

This is a plain, additive `manage.py migrate` — the same command an
operator would run by hand. Nothing here ever flushes, resets, fakes, or
drops schema on startup; upgrading means pulling a new image and letting
Django's own migration graph bring the schema forward, in the same
dependency order it always resolves migrations in. A newer build's
container simply refuses to start if its migrations can't apply cleanly,
rather than silently reinterpreting or discarding existing data.
`tests/compatibility/test_migration_discipline.py` guards both of these
as a regression: the entrypoint never gains a destructive command, and
every app's migration graph has exactly one leaf (no unmerged branches a
plain `migrate` could apply in an ambiguous order).

## Data migration: backup and restore

Before any upgrade, back up authoritative state:

For quiesced snapshots with integrity manifests and post-restore verification,
see [verified backup checkpoints](BACKUP_CHECKPOINTS.md). The Core commands below
remain available.

```
make backup                    # -> backups/<timestamp>/
make backup DEST=/path/to/dir  # or a caller-chosen destination
```

This covers PostgreSQL (a `pg_dump --format=custom`) and the object
store's raw volume (artifacts, not their metadata, which lives in
Postgres). Valkey is never included — disposable cache/broker state only,
per `config/settings.py`'s own comment on `VALKEY_URL` — restoring it
would be meaningless, and a fresh instance rebuilds it on its own.

Restore the same way:

```
make restore DEST=backups/<timestamp>
```

`make backup-restore-smoke` proves the round trip actually recovers real
state (not just "the commands didn't error"): it seeds a uniquely-named
workspace, backs up, deletes the workspace, restores, and confirms it (and
only it) is back. See `scripts/backup-restore-smoke`.

## Canonical archive (`format_version`)

Exporting/importing an event, saving/instantiating an event template, and
cloning an event all go through the same canonical archive described in
`docs/architecture/CANONICAL_ARCHIVE.md`. Its `format_version` is the
compatibility contract for _that_ document, independent of the database
schema above: a build only ever reads the `format_version` values it was
written to understand, and an archive from an incompatible version is
rejected outright with a named error, never silently reinterpreted.

## API versioning

Every application route lives under `/api/v1/`, per
`docs/api/CONVENTIONS.md`. A breaking change to a route's request/response
shape is a new version prefix, not a silent change to `v1` — nothing in
this codebase does that yet, but the moment it needs to, this is where
that decision gets recorded.

## Prior-schema migration smoke fixture

`demo/release-freeze` (PostgreSQL 17 dump from the 2026-09-27 release rehearsal, checksum in its
`MANIFEST.md`) is the recorded prior released schema. `tests/compatibility/test_prior_schema_migration_smoke.py`
restores it into a scratch database, runs a normal `manage.py migrate` with the current code, checks
`migrate --check` is clean, and asserts the five records named in the manifest (event, project,
submission version, ballot, award) read back exactly once. It runs when `DATABASE_URL` is PostgreSQL
and a `pg_restore` that can read the dump is available (local, else Docker `postgres:17`, override with
`CONFLUX_PG_RESTORE_IMAGE`); otherwise it skips with the reason. A companion test pins the dump's
SHA-256 so the fixture cannot drift silently. When a newer release ships, add its dump next to this one
and extend the test rather than replacing the record of the older release.
