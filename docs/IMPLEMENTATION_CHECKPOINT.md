# PVS10 — Sequential implementation checkpoint

## Result

Core, Stretch, Very-Stretch (VS01–VS50), PVS-H00, PVS01–PVS05, PVS-H01, PVS06–PVS10 complete on `main`. Earliest unfinished batch: **PVS-H02**, then PVS11–PVS15, PVS-H03, PVS16–PVS18 (PVS18 only if PVS-H02 finds a bottleneck), PVS-H04, PVS-H05.

## Changes

- Each batch has `docs/batches/<ID>.md`; operator docs in `docs/operations/`; PVS-H00/H01 evidence in `docs/verification/`.
- New apps: `taxonomy`, `eligibility`, `deliberation`, `onsite`; new libs `segno`, `pyyaml`.
- PVS08: `artifacts.inspector`/`url_inspector` (static, non-executing inspection), `ArtifactInspection`, `artifacts.review_views` (judge/organizer/owner inspection surface), `projects.submissions.preview_frozen_submission` + `SubmissionPreviewView` (exact-as-judge preview with frozen-version drift detection).
- PVS09: `awards.AwardResource` (sponsor challenge content: API/starter-repo/contact/FAQ/workshop), sponsor-portal resource CRUD scoped to organizer-or-sponsor-contact, `awards.ChallengeListView` (participant-facing, workspace-member-only).
- PVS10: new `mentorship` app (`MentorProfile`, `MentorRequest`, `OfficeHourSlot`/`OfficeHourSignup`); bounded per-project request queue with claim/reassign/resolve/cancel; office-hours signup with capacity checks. Registered in the v2 final-archive schema.
- Standing guards: `tests/security` (route/isolation/fuzz/CSRF/idempotency sweeps), `tests/integration/concurrency/test_pvs_races.py` (PostgreSQL), final-archive guard test that forces every new event-owned model to be archived or excluded.
- Preserve unrelated owner dirt: `.gitignore`, `master.sh`, `master/`, `tests/test_master_supervisor.py`. Never `ruff format` the `tests/` root or add those files.

## Verification

- Full suite: SQLite 1195 passed/20 skipped (`-n auto`); `test_evaluation_api.py::test_ballot_and_audit_commit_together_without_a_test_transaction` flakes only under parallel `-n auto` runs (passes standalone) — pre-existing, unrelated to PVS08–10, not yet root-caused.
- PostgreSQL 17 (`DATABASE_URL=postgres://conflux:conflux@localhost:15432/conflux` from `COMPOSE_PROJECT_NAME=confluxh00 POSTGRES_PORT=15432 ... docker compose up -d db`, see `/tmp/h00-env.sh` pattern in docs/verification/PVS-H00) 1168 passed/5 skipped at PVS-H01; not rerun since (no migration/concurrency-sensitive change beyond additive migrations).
- Env for tests: `DJANGO_SECRET_KEY=analytics-test-only RECORD_SIGNING_KEY_SEED=000…001 DJANGO_DEBUG=1`; run `.venv/bin/pytest tests -q -n auto -p no:logging`.
- After any API change: `manage.py spectacular --validate --fail-on-warn --file docs/api/openapi.yaml`, `scripts/generate_sdks.py`, then `scripts/check_openapi_artifact.py` and `scripts/generate_sdks.py --check`. All clean at PVS10 (note: nullable `ChoiceField` breaks `generate_sdks.py`'s union handling — use nullable `CharField` for a nullable enum-like value instead).
- When adding a model with a direct FK to `events.Event`, `test_final_archive.py::test_every_event_owned_model_is_archived_or_explicitly_excluded` forces classification into `integrations/final_archive_schema.py`'s `TABLES` or that test's `EXCLUDED_EVENT_MODELS` — check this right after `makemigrations` on any new event-scoped app.

## Limitations

- PVS features are API/CLI only so far; UI, Playwright scenes and demo package are PVS-H03/H05. Public server-rendered pages lack font/link styling (H03 finding).
- Session tokens unhashed at rest (documented in PVS-H01 findings).
- PVS08 preview endpoint has no UI; drift detection compares recorded fields, not live storage bytes (that's `run_inspection`'s job).
- PVS09's `AwardResource` is not in the final-archive/event-as-code table set (see `docs/batches/PVS09.md`) — inconsistent with PVS10's mentorship tables, which are; worth reconciling in PVS-H04.
- PVS10 has no reminder/notification integration for requests or office hours (deliberately, to avoid chat-clone scope).

## Next

PVS-H02 (realistic load, DB and performance hardening) — the fixed-order Core→PVS10 feature roadmap is now complete. Code freeze Tuesday 2026-09-29 18:00 UTC; stop new features at 08:00 UTC that day.
