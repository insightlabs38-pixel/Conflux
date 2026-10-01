# Background jobs (ASYNC_JOB)

One durable job model for anything too long for a request. A feature registers a **kind** and enqueues; it never adds its own job table, status field or polling endpoint. Code: `core/jobs.py` (contract), `core/job_views.py` (endpoints), `core/tasks.py` (Celery), web `lib/jobs.ts` and `features/operations/JobsPanel.tsx`.

## Lifecycle

```
queued -> running -> succeeded | failed | cancelling -> cancelled
queued -> cancelled
```

Every change is under a row lock along `jobs.TRANSITIONS`; a finished job never changes again. A second delivery of the same job does nothing (only `queued` starts), so a duplicate Celery message, a cancel racing the start and the stale sweep cannot disagree.

- **Cancel** is cooperative. A queued job is cancelled at once. A running one becomes `cancelling` and ends when its handler next calls `ctx.checkpoint()`. The platform never kills work mid-write and never rolls back what a handler already did; a handler that must be all-or-nothing wraps its own writes in one transaction. A handler that finishes despite the request is `succeeded`, because that is what happened.
- **Timeout**: a running job that reports nothing for its kind's `timeout` (default 300 s) is failed with code `timeout` by the sweep (beat, every 60 s). A stale `cancelling` job is `cancelled`. Queued jobs older than 60 s are re-sent to a worker, which covers a lost message or a broker outage at enqueue time.
- **Failure shape**: `{code, message}`. A `ValidationError` raised by a handler is shown (`invalid`); anything else is `internal` with a generic message, and the detail stays in the server log. Other codes: `timeout`, `forbidden` (the requester lost the role before the job ran), `unknown_kind`, `unsafe_result`.

## Registering a kind

```python
from core import jobs

def handler(ctx):                      # ctx.params, .event, .workspace, .actor
    for i, item in enumerate(items):
        ctx.checkpoint()               # raises if the user cancelled
        ctx.progress(i, len(items), "Processing")
        ...
    ctx.artifact("report.csv", "text/csv", data)   # <= 25 MB, kept with the job
    return {"rows": len(items)}                   # <= 64 KB JSON

jobs.register_kind(jobs.JobKind("my_kind", "My report", handler,
                                roles=(Role.ORGANIZER, Role.ADMIN), params=MyParams))
```

Register in the app's `AppConfig.ready()` (see `integrations/apps.py`) so both the web process and the worker know the kind. `enqueue(kind=, actor=, workspace=, event=, params=, idempotency_key=)` returns `(job, created)`. The feature's own endpoint calls it and answers **202 with `jobs.describe(job)`**.

- `params` are validated by the kind's serializer, at most 16 KB, and **secrets never belong in params, results or logs**: a key containing password, secret, token, api_key, authorization or credential is refused in params and fails a job whose result has one.
- **Idempotency**: the same `(requester, kind, key)` returns the existing job (HTTP 200 instead of 202); the same key with different input is a 400. Keys never cross people.
- **Limits**: 10 unfinished jobs per person; logs keep the newest 500 lines; artifacts 25 MB each.
- Handlers run outside any transaction opened by the platform, so `progress`/`log` are visible while it works. Never start external delivery you cannot repeat without an idempotency story of your own: a job can be re-sent before it starts, never after.

## API

| Call                                              | Notes                                                                          |
| ------------------------------------------------- | ------------------------------------------------------------------------------ |
| `GET /workspaces/{w}/jobs/`                       | `event`, `kind`, `status`, `limit` (1-100), `offset`; total in `X-Total-Count` |
| `GET /workspaces/{w}/jobs/{id}/`                  | adds `params` and `logs`                                                       |
| `POST /workspaces/{w}/jobs/{id}/cancel/`          | 400 when already finished                                                      |
| `GET /workspaces/{w}/jobs/{id}/artifacts/{name}/` | attachment, `nosniff`, `no-store`                                              |

Visibility: the requester sees their own jobs; organizers and admins see the workspace's. Anyone else gets 404 (never 403) so a job's existence does not leak. Starting and cancelling are audited (`job.requested`, `job.cancel_requested`, `job.cancelled`, `job.succeeded`, `job.failed`).

## First adopter: event archive export

`POST /workspaces/{w}/events/{e}/archive/export-jobs/` with `{mode: config|full|final, signed: bool}` and an optional `Idempotency-Key` header runs the same export as `GET .../archive/` (which stays, unchanged) as a background job and keeps the file as an artifact. In the web: Operations > Exports and jobs. Not moved: archive import and the event simulator stay synchronous (they are request-bound, validated against the caller and need an immediate answer) and are listed in spec 002.

## Web

`lib/jobs.ts` `followJob` polls (0.7 s growing to 4 s), reports progress into `useOperation`, tolerates two failed polls in a row, and turns a user cancel into a server cancel request. It never marks anything finished on its own. Reopening the page shows the same job from the list; there is no push channel yet (polling only).

## Compatibility and migration

Additive: tables `core_job`, `core_jobartifact`, `core_joblog` (migration `core/0003_jobs`), new endpoints, no change to an existing response. The three Celery tasks (webhooks, reminders, artifact scan) keep running as they are and are not jobs: they are recurring system work with no requester. `core.job` is excluded from the event archive (operational state; the audit trail is the record).

## Known limits

No retention sweep (jobs and artifacts are kept; artifacts live in the database, so a very large export belongs behind object storage in a later task), no automatic retry of a failed job (retry is a new, deliberate request), no push updates, no job scheduling or priorities, and concurrent workers rely on row locks (PostgreSQL; SQLite runs the same code single-threaded).
