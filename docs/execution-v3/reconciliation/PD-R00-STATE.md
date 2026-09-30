# PD-R00 Reconciliation Record — Git/runtime state (T03) and plan-vs-repo delta (T05)

Recorded 2026-09-30T05:04:06Z by the continuous single agent (claude-sonnet-5-5, controller epoch 1).

## T03 — Git / runtime state
- Canonical branch `main`; HEAD at start of PD-R00: `feb248c` (activation commit); activation base `5680dcd`. `main` is 2 commits ahead of `origin/main` (unpushed; push is not authorized by the program).
- Working tree at start: only untracked `conflux_v3_claude_design_handoff{,_r2,_r2_1}.zip` (design inputs; left untouched, untracked).
- Worktrees/branches from the abandoned DOGFOOD lanes: `claude/C-B02` (`~/conflux-worktrees/claude-C-B02`), `sol/C-B04`, `freebuff/RT-001`, plus branch `sol/BOOT-B00`. Each is clean and **0 commits ahead of `main`** (fully merged). Kept as historical; **quarantined by LINEAGE.md**, not v3 claims. Not deleted (non-destructive rule).
- `.dogfood/master.pid` = 860048: process not running (stale, git-ignored). No live DOGFOOD master or worker.
- v3 claims/handoffs/escalations at start: none (`recovery_report.py`: CLAIMS 0, OPEN_ESCALATIONS 0, HANDOFFS 0). No merge markers in tracked files (`rg '^(<<<<<<<|>>>>>>>) '` empty). No stashes.
- Runtime overrides at activation: `TASK_STATE` = {PD-R00-T01: READY}, `BATCH_STATE` = {PD-R00: IN_PROGRESS}; `PROGRAM_STATE` ACTIVE epoch 1 (controller-owned; stale "not activated" note refreshed).
- Single live process of note: `scripts/claude_supervisor/supervisor.py` (pid 654256), waiting for its 02:50 EDT window; its headless session resumes from repo state.

## T05 — Plan-versus-repository delta (inputs for PD-B00; nothing marked DONE)
Method: every batch `owned_paths` prefix checked for existence; queue subsystems compared to `src/api` apps, `src/web/features`, `tests/`, `docs/api`.

**Layout facts.** Backend = Django apps under `src/api/<app>`; frontend = `src/web/{features,components,lib,hooks,blocks}`. 87 distinct owned-path prefixes across 331 batches do not exist yet. They are almost all *new* module directories (create-on-first-use), not moved paths, e.g. `src/api/{operations,search,analytics,bulk,sponsors,scheduling,registration,organizations,staffing,configuration,notifications,storage,mcp,simulations,moderation,expenses,inventory,archives,publication,diagnostics,i18n}`, `src/web/components/data-grid`, `src/web/features/{projects,search,sponsors,schedule,onsite,organizations,staffing,extensions,participant-hub,inventory,closeout,analytics,registration,mentorship,notifications,permissions,governance}`, `docs/extensions`.

**Existing implementations that overlap named future work (audit/reuse/migration candidates for PD-B00 or the owning subsystem; not closed):**
| Queue area | Existing code/evidence | Class |
|---|---|---|
| S012 registration/waitlists | `src/api/events/registration.py`, `registration_views.py`, migration 0002 (invite codes, settings) | audit; path `src/api/registration` is a *new* home → decide extend-vs-move |
| S017 artifact storage | `src/api/artifacts/storage.py`, `tests/storage/test_s3_contract.py` | audit/reuse; `src/api/storage` prefix is new |
| S043 analytics | `src/api/communications/analytics*.py`, `docs/api/EVENT_ANALYTICS.md` | audit/reuse |
| S049 MCP | `src/api/mcp_adapter/`, `docs/operations/MCP.md`, `scripts/conflux_mcp_stdio.py` | audit; queue path `src/api/mcp` ≠ existing `mcp_adapter` (path reconcile) |
| S067 moderation | `src/api/communications/moderation.py`, `docs/api/MODERATION.md` | audit/reuse; queue path `src/api/moderation` new |
| S039/S105 publication | `src/api/presentation` (PublicationSchedule), `docs/api/PUBLICATION_SCHEDULING.md` | audit; queue path `src/api/publication` new |
| S046 Event-as-Code | `src/api/config`, `tests/integration/test_configuration_rollback.py`, `scripts/conflux-admin` | migration/audit; queue path `src/api/configuration` ≠ existing `config` (path reconcile) |
| S038/S041 search | `docs/api/PUBLIC_SEARCH.md`, public gallery code | audit |
| S053 permissions | `src/api/events/permission_matrix_views.py`, `accounts` | audit/migration (authz is high-risk; serialize) |
| S035 onsite | `src/api/onsite`, `events/checkin_views.py` | audit |
| S051 webhooks | `src/api/integrations`, `docs/api/WEBHOOKS.md` | audit |
| S033 mentorship | `src/api/mentorship` | audit |
| S050 extensions | `src/api/extensions` | audit; `src/web/features/extensions`, `docs/extensions` new |
| S016/S065 forms/taxonomy | `src/api/forms`, `src/api/taxonomy`, `src/web/features/form-builder` | audit/reuse |
| S052 import/export | `src/api/artifacts/portability.py`, archive v4 (see IMPLEMENTATION_CHECKPOINT) | audit/migration (archive-format lock) |
| S058 i18n | `src/api/locale` | audit; queue path `src/api/i18n` ≠ `locale` |
| S006 data grid | `src/web/components/*` (no data-grid) | new |

**Path reconciliation applied:** none in `TASKS.yaml`/`BATCHES.yaml` (owned_paths are ownership globs that may legitimately name not-yet-created dirs; rewriting 3110 tasks would be unsafe). Workers must treat the three "≠ existing" rows (`mcp`↔`mcp_adapter`, `configuration`↔`config`, `i18n`↔`locale`) as extend-existing-app unless the subsystem spec says otherwise; PD-B00 should confirm.

**Not covered here (PD-B00):** defect census, test baseline, depth grading of any listed implementation.
