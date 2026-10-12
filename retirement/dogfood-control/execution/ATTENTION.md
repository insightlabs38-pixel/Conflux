# HIGH ATTENTION

## C-B01 complete: RT-001..RT-004 all done
**2026-09-26T22:40:00+00:00 (sole sequential worker, no scheduler restarted):** RT-002 (health checks + dependency ordering) and RT-003 (make targets + fast dev overlay) committed to `main` (`588160e`, `3070a63`) and pushed. While wiring RT-002's worker healthcheck, found and fixed two real pre-existing defects: `config` had no Celery app at all (the `worker` service's `celery -A config worker` entrypoint would have failed on boot — RT-001 composed the service but this was apparently never actually run), and kombu's redis transport needs the `redis` package, which was never declared as a dependency. Both fixed and verified against real Postgres/Valkey containers, running Django/Celery from the host venv.

**RESOLVED 2026-09-26T22:57:00+00:00 (sole sequential worker):** The sandbox-network restriction blocking RT-004 (PyPI/npm unreachable from inside a container) had cleared — re-verified live (`pypi.org`/`registry.npmjs.org` both 200, a plain `python:3.12-slim` container installed `uv` over the network). Ran `docker compose up -d --build`: all 6 services (app, worker, db, cache, objectstore, caddy) reached healthy. Found and fixed one real defect along the way: `INSTALLED_APPS` was missing `django.contrib.staticfiles`, which the entrypoint's `manage.py collectstatic` step needs. Added `docker-compose.offline-smoke.yml` + `scripts/cold-offline-smoke` (`make cold-boot-smoke`): reuses the built images and runs the compose network as `internal: true`, proving the *running* stack (not just the build) needs zero hosted dependency — the actual claim behind the challenge's one-command/network-off rule. Host-published-port access didn't route under `internal: true` in this sandbox's Docker networking (an environment quirk of this sandbox, not a product defect — container-to-container traffic worked fine); the smoke script instead asserts end-to-end health via `docker compose exec caddy curl` from inside the internal network. `make verify-fast` passes. Committed `0499b51`, pushed. C-B01 is complete; see `execution/receipts/RT-004.json`.


## C-B02 integration is deferred
The integration controller previously looked up batch IDs as task IDs, so it reported all C-B02 files outside ownership. Batch lookup is fixed. C-B02 also changed `src/api/config/settings.py`, explicitly listed in its receipt as an out-of-scope touch. RT-001 currently holds `src/api/config/**`; do not integrate C-B02 until RT-001 releases that lease and the settings change receives ownership review. C-B02's `tests/integration/**` path is now covered by its batch ownership.

**RESOLVED 2026-09-26T21:15:00+00:00 (manual reconciliation, no scheduler restarted):** C-B02 fast-forward-merged into `main` at `cb6d3df`; clean, no conflicts (main had not moved since C-B02 branched).

## C-B04 requires integration review
C-B04 is committed on `sol/C-B04` with a `needs-review` receipt. Its runtime registration needs `src/api/config/settings.py` (held by RT-001), `src/api/core/urls.py`, and `src/web/app/App.tsx`, none of which are in C-B04's owned paths. Keep the receipt and reservation in review; do not claim the batch complete until an authorized integration change registers the app, API routes, and UI.

**RESOLVED 2026-09-26T21:15:00+00:00:** `sol/C-B04` merged into `main` (commit `94c0949`), then wired live: `events` added to `INSTALLED_APPS`, `events.urls` included under `/api/v1/` in `core/urls.py`, `EventDashboard` mounted from `App.tsx` behind a `?workspace=` query param (no workspace-selection UI exists yet, so this is the minimal honest entry point). Wiring committed as `0469784`. `make verify-fast` passes, including `EventDashboard.test.tsx` now that it's actually reachable. Receipt updated to `done`.

## Codex auth classification
The previous Sol auth pause was a false positive: classifier matched `unauthorized` in application test output despite a completed Codex turn. The classifier now treats a completed turn as success and excludes the generic word. Codex login currently reports `Logged in using ChatGPT`; Luna is polling and has no safe eligible task.

## RT-001 (freebuff) — recovered and integrated
RT-001's worktree at `/home/insightlabs38/conflux-worktrees/freebuff-lane` had uncommitted compose/runtime changes (docker-compose.yml, pyproject.toml, settings.py, uv.lock, plus untracked .dockerignore/.env.example/infra/) and no receipt; Freebuff's TUI submission was never confirmed. Nothing was discarded: the changes were committed on `freebuff/RT-001` (`c65819e`), formatting issues (ruff/prettier) fixed in follow-up commits, then merged into `main` (`628a08a`). The one real conflict, `src/api/config/settings.py`, was hand-merged: RT-001's env-driven DATABASE_URL/VALKEY_URL/S3_*/ALLOWED_HOSTS/STATIC_ROOT restructuring was kept alongside C-B02's `INSTALLED_APPS` additions and `AUTH_USER_MODEL`. A receipt was written to `execution/receipts/RT-001.json` (status `done`). OWNERSHIP.yaml's `freebuff/RT-001` lease and `sol/C-B04` reservation are both released — see `completed_batches`.

## C-B04 follow-up: workspace-selection UI
**RESOLVED 2026-09-26T21:45:00+00:00:** The event dashboard was reachable only via a manually-typed `?workspace=` query param. Added `src/web/app/WorkspaceSelector.tsx` (lists the current user's authorized workspaces from the existing `accounts/me` + `Membership` model, no new authorization logic) and wired it into `App.tsx` as the default view; selecting a workspace updates the URL via `history.pushState`. Direct `?workspace=` links, including invalid/unauthorized ones, are preserved and always show a "Back to workspaces" escape hatch. `accounts/me` now additively returns `workspace_name`/`workspace_slug` per membership. Added a nonexistent-workspace-id 404 test to `events/test_events.py` and a `happy-dom` dev dependency for effect/fetch-driven frontend tests (the existing static-render test style can't exercise this). `make verify-fast` passes. Commit `45c5eb3`, pushed to `origin/main`.

## Integration order used
`main` -> fast-forward to `claude/C-B02` -> merge `freebuff/RT-001` (settings.py hand-merge) -> merge `sol/C-B04` -> wire events runtime registration. All pushed to `origin/main` at `0469784`. `freebuff/RT-001` branch also pushed with its new commits (no force-push, no history rewrite).

## Flagged: events API has no coverage in the default test suite
Found while working ST-001 (unrelated area, noted rather than fixed to stay in scope): `src/api/events/test_events.py` (C-B04) targets bare `/workspaces/<id>/events/...` paths under its own isolated `events.testing_settings` (`ROOT_URLCONF = events.urls`, no `/api/v1/` prefix) and needs `--ds=events.testing_settings` to run. `pyproject.toml`'s `testpaths = ["tests"]` never collects it, so `make verify-fast`/`pytest -n auto` exercise zero real events-API endpoints — `tests/integration/test_bootstrap_api.py::test_unimplemented_product_route_is_not_advertised` (`GET /api/v1/events/` → 404) still passes only because that literal bare path was never a real route (all real event routes are `/api/v1/workspaces/<id>/events/...`); it isn't evidence the mounted API is exercised. Worth a small follow-up: port a subset of test_events.py into `tests/integration/` against the real `/api/v1/` prefix, or fix testpaths/settings so the existing file runs for real.

## Not touched, left for a human
- The `conflux-outcome-classify` and `conflux-integrate` tooling in `/home/dogfood-control/bin` were reviewed but not exercised — this reconciliation was done with plain `git` commands by hand, per instruction, rather than trusting the automated integration path.
- The retired master/timer/scheduler system was not restarted, and `run/bootstrap-green` was left untouched.
- Worktrees at `/home/insightlabs38/conflux-worktrees/{claude-C-B02,freebuff-lane,sol-C-B04}` and their branches were left in place (all three branches are now fully merged into `main`); deleting them was out of scope and not requested.

## C-B07 complete
TEAM-001..004 are committed and pushed on main through c74f5ca. TEAM-004 added participant event/team UI and invite API; 180 API and 11 web tests passed, and the rebuilt stack passed all 7 official acceptance checks. Next: C-B08 PRJ-001.

## C-B08 complete
PRJ-001 and FORM-001..004 committed/pushed on main through 3b4b6be. Durable Project/ProjectMembership, immutable FormVersion, typed/conditional scoped responses, organizer form builder/preview. make verify-fast: 209 API + 13 web tests; rebuilt stack and official acceptance 7/7 PASS. Next: C-B09 ART-001.

## C-B09 complete
ART-001..006 committed/pushed through c051afe. make verify-fast: 224 API + 16 web tests; shared S3 contract RustFS 3/3 and SeaweedFS 3/3; rebuilt stack and official acceptance 7/7 PASS. SeaweedFS stopped after opt-in compatibility run. Next: C-B10 SUB-001.

## C-B10 complete
SUB-001..006 committed/pushed through da35bc0. make verify-fast: 232 API passed, 3 opt-in skipped; 17 web passed. Rebuilt stack and official acceptance 7/7 PASS. Next: C-B11 UI-001.
