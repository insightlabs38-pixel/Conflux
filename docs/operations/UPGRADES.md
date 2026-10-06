# Upgrade and compatibility discipline

What an operator can expect when moving to a newer build of Conflux, and
what stays stable across that move.

## Moving to a build with the shared primitives (PD-F002-B01)

Additive only: migrations `core/0002_saved_views`, `0003_jobs`, `0004_approvals` and `0005_threads` add tables and change nothing that exists, so they apply on the normal startup `migrate` and a rollback to the previous image simply leaves them unused. Two new Celery tasks need the **worker and beat to be restarted on the new image** (`docker compose up -d --build` rebuilds all three services; the `app` container alone does not carry them): `core.tasks.run_job` and the beat entries `sweep-jobs` (every 60 s: fails jobs that stopped reporting, re-sends queued ones that never started) and `sweep-approvals` (every 5 minutes: marks lapsed approvals). Until the worker is updated, a started job (an archive export) stays queued, and the sweep, once beat is current, re-sends it. Approval gates are off for every existing event, so no behavior changes until an organizer turns one on. See [shared primitives](../architecture/SHARED_PRIMITIVES.md).

## Moving to a build with the second shared primitives (PD-F002-B02)

Additive only. One migration, `core/0006_notification_preferences`, adds a table that stays empty until a person changes a notification choice; until then every category keeps its default, so mail goes out exactly as before, and a rollback to the previous image leaves the table unused. No new Celery task or beat entry, so the worker and beat need no restart for this batch. Existing audit rows, job results and configuration history are unchanged (older rows simply have no provenance). New read-only endpoints (rich preview, artifact preview, version history and comparison, notification preferences, extensions) appear in the OpenAPI contract and the generated SDKs. **Startup now runs the extension manifest check**: `manage.py check` (so `migrate` and `runserver`) fails with `core.manifest.<code>` when a source declares something that is not registered, a requirement is unresolved, or a manifest asks for an unsupported `api_version`. A deployment that adds its own registry entries should declare them in a `<app>/manifest.py`; an entry that is registered but not declared is only a warning. See [extensions](EXTENSIONS.md) and [shared primitives](../architecture/SHARED_PRIMITIVES.md).

## Moving to a build with preview contexts (PD-F002-B03)

Additive only: no migration, no new Celery task and no change to an existing endpoint. One new read-only endpoint, `POST /api/v1/workspaces/{id}/preview-as/{surface}/` (organizers and admins), appears in the OpenAPI contract and the generated SDKs; it stores and sends nothing. The extensions inventory gains a `preview_surface` capability, and a deployment that registers its own preview surface must declare it in its `manifest.py` or `manage.py check` fails. See [preview contexts](PREVIEW_CONTEXT.md).

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

## Moving to a build with the completeness contract (PD-F003-B01)

No migration, no new Celery task and no new endpoint beyond one read-only report, `GET /api/v1/workspaces/{id}/completeness/` (organizers and admins), which lists which of fifteen features provides which properties and checks every claim against the running system. See [completeness](COMPLETENESS.md). Four changes are visible outside that page:

- **More changes are audited.** Project, form, evaluation-plan, artifact, submission-draft, application-decision and team writes now write an audit row in their own transaction (`project.created`, `project.updated`, `form.created`, `form.draft_saved`, `evaluation_plan.updated`, `evaluation_plan.deleted`, `artifact.added`, `artifact.upload_started`, `artifact.uploaded`, `artifact.validated`, `submission.draft_saved`, `application.decided`, `team.created`, `team.member_joined`, `team.member_left`, `team.captain_transferred`, `team.invite_created`, `team.invite_revoked`, `team.invite_redeemed`). Rows hold ids and field names, never content, object keys, signed URLs or invite tokens. A submission autosave now adds one row per save.
- **Four creates accept an `Idempotency-Key`**: sending a message, posting an announcement, creating a project and adding an external artifact. It is opt-in: a request without the header behaves as before.
- **The OpenAPI document and both SDKs were corrected.** Ten list operations (announcements, artifacts, evaluation plans, events, forms, policies, projects, stages, team invites, tracks) were documented as one record and are now arrays, so a TypeScript or Python client that worked around the wrong type should drop the workaround; the message list documents its `offset`; the award output documents `resources`.
- **An empty-bodied 404 now carries `{"detail": "Not found."}`** (projects, artifacts, judging results and the scoreboard), with the same status.
