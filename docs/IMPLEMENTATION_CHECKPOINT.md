# PVS-H05 — Sequential implementation checkpoint (CAMPAIGN COMPLETE)

## Result

Core, Stretch, Very-Stretch (VS01–VS50), PVS-H00, PVS01–PVS05, PVS-H01, PVS06–PVS10, PVS-H02, PVS11, PVS12, PVS13, PVS14, PVS15, PVS-H03, PVS16, PVS17, PVS-H04, PVS-H05 complete on `main`. No unfinished batch (PVS18 skipped, see below); PVS-H04, PVS-H05. PVS18 skipped: H02 found no throughput bottleneck (only the fixed connection-bound bug).

## Changes

- Each batch has `docs/batches/<ID>.md`; operator docs in `docs/operations/`; PVS-H00/H01 evidence in `docs/verification/`.
- New apps: `taxonomy`, `eligibility`, `deliberation`, `onsite`; new libs `segno`, `pyyaml`.
- PVS08: `artifacts.inspector`/`url_inspector` (static, non-executing inspection), `ArtifactInspection`, `artifacts.review_views` (judge/organizer/owner inspection surface), `projects.submissions.preview_frozen_submission` + `SubmissionPreviewView` (exact-as-judge preview with frozen-version drift detection).
- PVS09: `awards.AwardResource` (sponsor challenge content: API/starter-repo/contact/FAQ/workshop), sponsor-portal resource CRUD scoped to organizer-or-sponsor-contact, `awards.ChallengeListView` (participant-facing, workspace-member-only).
- PVS10: new `mentorship` app (`MentorProfile`, `MentorRequest`, `OfficeHourSlot`/`OfficeHourSignup`); bounded per-project request queue with claim/reassign/resolve/cancel; office-hours signup with capacity checks. Registered in the v2 final-archive schema.
- PVS11: `governance` app (rules/acks, opt-in two-organizer publication approval, `ResultCorrection` history, `SubmissionReceipt`, assignment accept/decline via `ConflictOfInterest`, deadline-exception requests → `ExceptionGrant`); `check_action` now picks the newest _active_ grant. See `docs/operations/GOVERNANCE.md`.
- PVS12: optional OIDC in `accounts.oidc`/`oidc_views` (env-driven, lazy, PKCE, browser-bound state); see `docs/operations/SSO.md`.
- PVS13: `mcp_adapter` (credential-gated MCP over existing routes; `docs/operations/MCP.md`). Lint gate: `ruff check src/api tests scripts loadtests` must stay clean apart from owner's `tests/test_master_supervisor.py`.
- PVS14: read-only `portfolio` app (`docs/operations/PORTFOLIO.md`).
- PVS15: `continuation` app (`docs/operations/CONTINUATION.md`).
- PVS-H03: SPA now built into the image and served at `/app/`; sign-in form; Playwright suite in `tests/e2e` (needs a demo-seeded stack; `docs/operations/E2E.md`). Browser stack used: `COMPOSE_PROJECT_NAME=confluxh03 CONFLUX_PORT=28080 POSTGRES_PORT=25432 VALKEY_PORT=26379 S3_PORT=29000 S3_CONSOLE_PORT=29001`.
- PVS16: `onsite.AgendaSession`, public agenda/ICS/state/badge/map (`docs/operations/EVENT_LOGISTICS.md`).
- PVS17: read-only maintenance guard (`governance.maintenance`, monkeypatches `APIView.check_permissions` in `GovernanceConfig.ready`), `Project.gallery_visible/blocked`, CSV preview, self-export (`docs/operations/CONVENIENCE.md`).
- Standing guards: `tests/security` (route/isolation/fuzz/CSRF/idempotency sweeps), `tests/integration/concurrency/test_pvs_races.py` (PostgreSQL), final-archive guard test that forces every new event-owned model to be archived or excluded.
- Preserve unrelated owner dirt: `.gitignore`, `master.sh`, `master/`, `tests/test_master_supervisor.py`. Never `ruff format` the `tests/` root or add those files.

## Verification

- Full suite: SQLite 1289 passed/23 skipped (PVS13) (`-n auto`); `test_evaluation_api.py::test_ballot_and_audit_commit_together_without_a_test_transaction` flakes only under parallel `-n auto` runs (passes standalone) — pre-existing, unrelated to PVS08–10, not yet root-caused.
- PostgreSQL 17 (`DATABASE_URL=postgres://conflux:conflux@localhost:15432/conflux` from `COMPOSE_PROJECT_NAME=confluxh00 POSTGRES_PORT=15432 ... docker compose up -d db`, see `/tmp/h00-env.sh` pattern in docs/verification/PVS-H00) 1168 passed/5 skipped at PVS-H01; not rerun since (no migration/concurrency-sensitive change beyond additive migrations).
- Env for tests: `DJANGO_SECRET_KEY=analytics-test-only RECORD_SIGNING_KEY_SEED=000…001 DJANGO_DEBUG=1`; run `.venv/bin/pytest tests -q -n auto -p no:logging`.
- After any API change: `manage.py spectacular --validate --fail-on-warn --file docs/api/openapi.yaml`, `scripts/generate_sdks.py`, then `scripts/check_openapi_artifact.py` and `scripts/generate_sdks.py --check`. All clean at PVS10 (note: nullable `ChoiceField` breaks `generate_sdks.py`'s union handling — use nullable `CharField` for a nullable enum-like value instead).
- When adding a model with a direct FK to `events.Event`, `test_final_archive.py::test_every_event_owned_model_is_archived_or_explicitly_excluded` forces classification into `integrations/final_archive_schema.py`'s `TABLES` or that test's `EXCLUDED_EVENT_MODELS` — check this right after `makemigrations` on any new event-scoped app.

## Limitations

- Human-facing PVS workflows have UI (PVS-H06, [map](operations/PVS_UI.md)); technical/operator PVS features stay API/CLI-first by design.
- Session tokens are stored as keyed digests (PVS-H06); the public gallery is paginated (PVS-H06).
- Drift detection compares recorded fields, not live storage bytes (that's `run_inspection`'s job).
- PVS09's `AwardResource` is not in the final-archive/event-as-code table set (see `docs/batches/PVS09.md`) — inconsistent with PVS10's mentorship tables, which are; worth reconciling in PVS-H04.
- PVS10 has no reminder/notification integration for requests or office hours (deliberately, to avoid chat-clone scope).

## Next

Nothing autonomous. Campaign-complete signal created (`.dogfood/master.complete`). Demo: `docs/operations/DEMO.md`; evidence: `docs/verification/PVS-H04/`, `PVS-H05/`. Remaining human tasks: record the video from the runbook; optionally rotate secrets and set unique `.env` values for any real deployment.
