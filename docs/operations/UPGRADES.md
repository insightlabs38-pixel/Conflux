# Upgrade and compatibility discipline

What an operator can expect when moving to a newer build of Conflux, and
what stays stable across that move.

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

Once a prior released schema/fixture exists to migrate _from_ (there is
only one released version so far, so there is nothing to smoke-test yet),
`tests/compatibility/` is where that regression fixture and test belong,
following the same pattern as `test_canonical_archive.py` and
`test_migration_discipline.py` already in this directory.
