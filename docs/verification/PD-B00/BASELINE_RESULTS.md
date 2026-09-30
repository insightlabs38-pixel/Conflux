# PD-B00 Measured Baseline (T02–T08 appended below)

All commands from repo root at product SHA `e1888de` (code unchanged since). Env: `DJANGO_SECRET_KEY=bootstrap-checks-only`, `RECORD_SIGNING_KEY_SEED=bootstrap-checks-only-record-signing-seed` (as in Makefile). Raw logs: `logs/`.

## T02 — Fast/backend gate (SQLite default DB)

| Command                                            | Result                                          | Time                              |
| -------------------------------------------------- | ----------------------------------------------- | --------------------------------- |
| `uv run --frozen pytest -n auto --durations=30 -q` | **1400 passed, 23 skipped**                     | 78 s (8 xdist workers, 9m12s CPU) |
| `make format-check`                                | pass (after `.prettierignore` fix below)        | 21 s                              |
| `make lint`                                        | pass                                            | 5 s                               |
| `pnpm test`                                        | web 65 files / **168 tests** pass; embed 8 pass | —                                 |
| `make build`                                       | pass                                            | —                                 |
| `make sdk-check` (OpenAPI + SDK + sdk build)       | pass                                            | 6 s                               |
| `make block-schema-check`, `make i18n-check`       | pass                                            | <1 s                              |

**Doc drift:** README/final-pass claim 1373 backend + 137 web; measured 1400 backend + 168 web (more tests than documented).

**Skips (23):** 3 need `CONFLUX_S3_TEST_ENDPOINT`; 1 needs two S3 endpoints; 1 no prior released schema for upgrade smoke; 18 need PostgreSQL (row locks, FTS, multi-connection races) — covered by T03.

**Test-tail profile:** wall time is dominated by per-worker first-test setup, not slow tests. The 8 slowest entries are all `setup` at 7.5–8.0 s (one per xdist worker: DB creation/migration); the slowest real `call` is `tests/security/test_session_csrf.py::test_login_throttles_guessing_per_account_and_resets_on_success` at 7.0 s, then 3.3 s (`test_demo_scenarios`) and 2.8 s (`test_assignment_rebalance`). No test other than these exceeds 3.5 s. Optimization candidate (not applied; baseline only): reuse/copy a migrated template DB per worker.

**Defect found by this task (regression from PD-R00, fixed):** `make format-check` failed on 499 newly installed v3 control files (prettier). Fix: `.prettierignore` entries for the v3 bundle (precedent: `docs/execution/*.yaml`), and re-formatted the two `master/*prompt.md` banners and this dir. Re-run: pass.

## T03 — PostgreSQL 17 integration baseline

`DATABASE_URL=<isolated confluxh00 PG17 on :15432> uv run --frozen pytest -n auto -q -rs` → **1418 passed, 5 skipped**, 97 s. Django creates disposable `test_*` databases; the `conflux` DB on that instance and the running `conflux` stack DB (:5432) were not used. Skips (5): 3× S3 endpoint contract, 1× two-S3-endpoint portability, 1× prior-schema upgrade smoke (no released prior schema exists). All 18 PG-only tests skipped in T02 ran and passed here (concurrency races, row locks, FTS). Prior documented figure was 1391/5 (older commit).

## T04 — Playwright baseline and dependency census

Stack: running `conflux` compose project (backend `.py` tree hash identical to repo: `8761b4a2362e86c5`; frontend bundle not hash-compared). `./scripts/demo-reset` (12 s, checkpoint `submitted`, event `dc31fc8d-7069-548b-b761-f5774f55b125`) then `./scripts/e2e-fast` (all 18 spec files, 3 concurrent groups): **144 passed, 91 skipped, 0 failed, 3 m 48 s wall**. Groups: read-only 50 passed/2.0 m, public 48/2.0 m, stateful 40/3.0 m, final 6/46 s. Skips are the mobile project skipping desktop-only tests (per-test, by design). Serial `make demo-e2e` was not run (e2e-fast is the documented equivalent; serial is ≈ sum of groups ≈ 8 min). Raw: `logs/T04-*.log`.
Doc drift: `final-pass` reports 60 passed/11 skipped (submitted) + 39 (published); the suite is now larger (uiv2-* specs).

**Negative/boundary check:** re-running `lifecycle` without `demo-reset` fails at the first step with `locator.fill: Test timeout of 25000ms exceeded` (participant-24 already consumed) — no precondition guard or message (`logs/T04-negative-lifecycle-no-reset.log`). Defect D-01 below.

### Census (from spec inspection + run timings; time = summed test time)

| Class                                                 | Specs                                                                                                                                                                                                   | Notes                                                                                                                                      |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Read-only shared (safe to parallelize)                | signin, roles, extended-embed, workspace-shell, uiv2-surfaces, uiv2-gate, public, foundations, showcase                                                                                                 | read the seeded event; only local UI state (search/draft inputs, logout). workspace-shell 118 s and uiv2-surfaces 81 s are the long poles. |
| Shared-mutable, order/serial                          | event-themes (PATCHes event brand config, restores), profiles (PATCH own profile), participant-workflow (draft story), pvs (PUT deadline/RSVP/rules/mentor/volunteer state), uiv2-judge, uiv2-organizer | mutate the single demo event; idempotent-ish ("tolerates repeat") but not isolated.                                                        |
| Lifecycle canary (needs fresh `demo-reset submitted`) | lifecycle (serial; consumes participant-24, creates team/project, scores, publishes, awards), then uiv2-final-states (needs lifecycle's published state)                                                | strictly ordered; not re-runnable without reset.                                                                                           |
| Release-only / media                                  | scenes (screenshots + video), lifecycle & uiv2-final-states video (`video: "on"`)                                                                                                                       | run for handoff media (`scripts/package-demo-media`), not for regression signal.                                                           |
| Isolated (own workspace/event)                        | **none**                                                                                                                                                                                                | every spec targets `demo-hackathon-7`; concurrency comes only from grouping.                                                               |

Dependency findings: (1) a single mutable event is a shared fixture, so only the read-only group can scale out; per-spec isolated workspaces would allow parallelism and re-runnability. (2) `e2e-fast` group order encodes an implicit contract (`stateful` before `final`) that is only documented in the script comment.

## T05 — Representative UI surface census

Spec `tests/e2e/pdv3-baseline-census.spec.ts` (opt-in: `E2E_CENSUS=1`, skipped otherwise, so gates are unchanged). Run after `scripts/demo-reset`:
`E2E_CENSUS=1 E2E_GROUP=census npx playwright test -c tests/e2e/playwright.config.ts --workers=1 pdv3-baseline-census` → **15 passed, 2.1 min**.
Output `docs/verification/PD-B00/ui-census/`: **81 full-page JPEG captures + `manifest.json`** (3.7 MB) at desktop 1280×800 and mobile 390×844 for: sign-in and workspace selectors; public landing/gallery/results/agenda/map; organizer (11 views), judge (5), participant (6), participant without team (3 real empty states), mentor, volunteer; plus synthetic states: loading (identity request held open), error (events list forced 500), and a participant deep-linking to an organizer view.
Measured per surface (no assertions on quality): **0 WCAG 2.2 AA axe violations, 0 px horizontal overflow, 0 console/HTTP problems for authenticated surfaces** (signed-out shell logs an expected 401 on `/accounts/me/`).
Visual baseline read from captures: consistent left-nav role shell, plain neutral canvas, sparse empty/loading states ("Loading stages…" text box, bare selectors before an event is chosen), organizer/judge lists are plain rows, public gallery is initials tiles. Later batches compare against these files.
Limits: the public gallery is server-rendered so an API-mocked "empty" state is not representable; empty states come from `participant-23`. Judge/participant views require an event (and stage) selection which the harness performs.

## T06 — Documentation vs implementation reconciliation

Checks run: (1) relative-link scan of 255 tracked `.md` files outside v3 planning dirs: 84 relative links, **0 broken**; (2) every `/api/v1/...` path quoted in `docs/**/*.md` looked up in `docs/api/openapi.yaml` (338 paths; lenient prefix match): **0 missing**; `make sdk-check`/`openapi-check` pass (T02); (3) test-count claims vs measurements; (4) documented known limitations vs current UI code; (5) legacy execution docs (done in PD-R00).

| Finding                                                                                                                                                                                             | Action                                                                                                      |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| README test counts stale (1373/137 web; Playwright never stated)                                                                                                                                    | **Corrected in README.md** to measured 1400/23, PG 1418/5, 168+8 web/embed, Playwright 144/91 (D-02, D-07)  |
| `docs/verification/README.md` limitation says re-open the project to refresh the artifact picker; UI has a **Refresh included artifacts** button (`SubmissionPanel.tsx`) and remounts on tab change | **Corrected** (D-11). Live auto-refresh remains a real UX gap → spec 017/015                                |
| `final-pass/report.md`, `PVS-H06/report.md`, `UIV2-B10.md` counts (1391/1373/1366/1400)                                                                                                             | Historical receipts: **left verbatim**; each is correct for its own commit (UIV2-B10 already says 1400/168) |
| PVS_UI "API-only by design" list (deliberation stances/notes, sponsor portal writes, eligibility rule configuration, replay/capsule/SSO/MCP) vs v3 specs that promise UI for several                | Not a defect; **input for feature batches** (specs 025/029, 032, 021, 049/060)                              |
| `docs/execution/**`, `master/**` claim active authority                                                                                                                                             | Resolved in PD-R00 (LINEAGE.md)                                                                             |
| Not checked (out of bounds for a doc audit): prose feature claims in ARCHITECTURE/JUDGING/SECURITY were not re-derived from code; only measurable claims above were verified.                       |
