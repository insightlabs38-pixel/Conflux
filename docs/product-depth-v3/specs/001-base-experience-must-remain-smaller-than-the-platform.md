# PD-F001 — Base experience must remain smaller than the platform

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §1  
**Queue batches:** PD-F001-B01, PD-F001-B02

## Completion interpretation

This specification is the canonical depth contract for §1. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `POLICY_EXPLAIN`
- `QUERY`
- `RICH_DOC`
- `ROUTER`
- `SCHEMA_EDITOR`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | required |
| `sdk` | not_required |
| `cli` | not_required |
| `mcp` | not_required |
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | not_required |
| `archive` | not_required |
| `analytics` | not_required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- No dedicated visual reference is required by default. Any UI introduced still follows the global Conflux v3 design system.

## Minimum verification contract

For the subsystem as a whole:
- realistic happy-path data;
- malformed/boundary behavior with useful diagnostics;
- authorization/visibility boundaries;
- lifecycle and migration/compatibility behavior;
- retry/idempotency/concurrency for shared-state mutations;
- required browser states for UI-facing flows;
- no regression of canonical existing behavior;
- exact commands/results recorded in receipts.

## Non-goals / restraint

- No duplicate source of truth solely for a new surface.
- No redundant hash/signature/proof layer unless it enables a real portability, offline-verification or external-trust workflow.
- No LLM/AI decision authority for deterministic official state such as scores, permissions, deadlines, policy or winner selection.
- No participant surveillance or engagement gamification without a concrete event purpose.
- No replacement of a mature generic external product category when a bounded integration solves the event-specific need.

## Product requirements from research

A platform can contain 500 capabilities while a new organizer sees only 15 decisions.

- BASE: event creation starts from a high-quality preset with event name, dates, registration, team rules, project requirements, judging method, awards, and publish controls.
- BASE: advanced configuration stays collapsed until a feature requiring it is enabled.
- BASE: sane defaults are real defaults, not placeholder values requiring organizer cleanup.
- BASE: disabled systems disappear from navigation rather than presenting empty tabs.
- BASE: one canonical “event readiness” surface explains what is missing before launch.
- ADV: organizers can progressively switch from presets to custom workflows.
- EXPERT: every default can eventually be overridden where domain invariants permit.
- PROG: defaults and derived values are queryable so automation never has to reverse-engineer UI behavior.
- PROG: generated configuration includes explicit values only when necessary; inherited defaults remain legible.
- BASE: destructive or high-impact operations show consequences, not generic “Are you sure?” dialogs.

## Batch scope

### PD-F001-B01 — Base experience must remain smaller than the platform — event creation starts from a high-quali… → defaults and derived values are queryab…

- event creation starts from a high-quality preset with event name, dates, registration, team rules, project requirements, judging…
- advanced configuration stays collapsed until a feature requiring it is enabled
- sane defaults are real defaults, not placeholder values requiring organizer cleanup
- disabled systems disappear from navigation rather than presenting empty tabs
- one canonical “event readiness” surface explains what is missing before launch
- organizers can progressively switch from presets to custom workflows
- every default can eventually be overridden where domain invariants permit
- defaults and derived values are queryable so automation never has to reverse-engineer UI behavior

### PD-F001-B02 — Base experience must remain smaller than the platform — generated configuration includes explic… → destructive or high-impact operations s…

- generated configuration includes explicit values only when necessary; inherited defaults remain legible
- destructive or high-impact operations show consequences, not generic “Are you sure?” dialogs


## PD-F001-B01 canonical contract (T00, 2026-09-30)

Evidence for every statement about current behavior: `docs/verification/PD-F001-B01/T00-census.log` (`probe_census.py`, read-only, run against the live stack's 9 persisted events and the 5 library presets instantiated inside a rolled-back transaction). Escalation for the two plan defects found: `docs/execution-v3/escalations/ESC-20260930-002.yaml`.

### What exists today (census)

- **Two readiness sources that disagree.** `EventDashboardView.configuration_checks` (events/views.py: dates, a track, a base prize) and `communications/checklist.py compute_launch_checklist` (7 rules: dates, forms, gate windows, voting window, rubrics, judge pools, public page). They share no rule ids and no rule code; on all 9 persisted events they disagree (dashboard says "configure a base prize", checklist says "no judges"). The operator console and the OperationsCenter read the checklist, the Setup tab reads the dashboard checks. Neither gates `draft → open`; only `Event.clean` (dates present, end in the future) does.
- **Four unrelated "preset" notions.** `integrations/template_library.LIBRARY` (5 event formats), `evaluations/workflow_presets.PRESETS` (two/three-round stage graphs), `policies/presets.PRESETS` (policy shapes) and the workspace-saved `EventTemplate` (config-mode archive). Only the first creates an event.
- **Presets are not usable defaults.** Each library preset instantiates a draft that is `blocked` on day one (no dates, no rubric published, no judge pool), has **no** `EventRegistrationSettings` row, no base prize and only placeholder-grade tracks (`Software`/`Hardware`). The Create-event form itself asks only for name and slug; everything else is discovered later in panels.
- **Navigation shows every destination.** `WorkspaceNavigation.roleDestinations.organizer` is a static list (10 destinations). An organizer on an event that uses none of On-site, Integrations or Eligibility review still sees all three. In the persisted data (module probes of `eventconfig/modules.py`, `T04-census.log`): public page 9/9 events, on-site 6/9, eligibility review 6/9, mentorship 6/9, community voting 3/9, deliberation 1/9, integrations 0/9. (The T00 census log used a rules-row probe for eligibility and so reported 0/9; `T04-census.log` supersedes it.)
- **Base decisions are scattered.** Team size and required artifacts live in `EligibilityRules` (an "eligibility" row), registration in `EventRegistrationSettings`, judging method in `EvaluationPlan` + published `RubricVersion` + `EvaluationPool`, awards in `BasePrize`, publish controls in `Event.status`/`is_public`/`Page`. No single place answers "what is this event's effective configuration and why".

### Canonical model (decision)

One rule governs everything below: **domain rows stay the only source of truth for values; the new layer describes, derives and explains, and persists only state with its own lifecycle.** No second settings store, no generic `PATCH` that bypasses domain serializers.

New Django app `eventconfig` (`src/api/eventconfig/`), additive migrations only:

1. **Setting registry** (`registry.py`, code, versioned). One `SettingSpec` per configurable value: `key` (`registration.mode`), `module`, `tier` (`base|advanced|expert`, the research tiers), `label`, `help`, `field` (the domain `model.field` that stores it), `type` descriptor (JSON-Schema-compatible: type/enum/minimum/maximum), `default` (a value or a named pure derivation, e.g. `ends_at = starts_at + preset duration`), `write` (the existing operation/endpoint that changes it), `lock(event) -> Reason | None`. The registry is the answer to "defaults and derived values are queryable" (T08) and the input to readiness (T05) and overrides (T07).
2. **Preset** (`presets.py`, code, versioned `(key, version)`): a declarative bundle of setting values and structural seeds (tracks, stage graph, evaluation plans, registration row, prize) for one event format. A preset **composes** the existing building blocks by reference (`workflow_presets` keys, `policies/presets` keys); it never redefines them. `template_library.LIBRARY` is migrated into it; `list_library` / `instantiate_library_template` and the template endpoints keep their shape and delegate (compatibility). Presets apply **only when an event is created** (one atomic synchronous transaction, the existing `instantiate_library_template` contract); re-applying a preset to a configured event is out of scope (S008).
3. **`EventProfile`** (one-to-one with `Event`): `preset_key`, `preset_version`, `created_at`. Provenance only. Legacy events have no row (= `custom/legacy`).
4. **`EventModuleSetting`** (`event`, `module`, `enabled`, `changed_by`, `changed_at`; unique on `(event, module)`): explicit organizer intent for an optional module. Effective enablement is computed: **`enabled = explicit-enabled OR in_use(event)`**, and a module cannot be disabled while `in_use`. So nothing with data ever disappears, disabling never deletes, and a legacy event with no rows behaves as if each module with data were enabled.
5. **Derived (never stored):** `source` of a value (`inherited` when it equals the preset/registry baseline, `overridden` otherwise, `derived` for computed ones), `in_use` per module, `workflow_source` (`preset` while the stage graph equals the preset baseline, else `custom`), and readiness.

**Module catalog** (nav `destination`, in-use evidence; `core` modules are always on and not toggleable):

| Module | Destination / panel | In use when | Notes |
|---|---|---|---|
| core | overview, setup, participants, judging, results, communications, operations | always | team size/required artifacts are **base** settings (stored in `EligibilityRules`) and do not make `eligibility_review` "in use" |
| `eligibility_review` | destination `eligibility` | any `EligibilityReview`/`EligibilityFinding`, or `rules.require_clearance` | |
| `onsite` | destination `onsite` | any `Location`, `AgendaSession`, `Attendance` | |
| `integrations` | destination `integrations` | webhook subscription, retention policy, qualifier binding/import | "Advanced" nav group |
| `community_voting`, `mentorship`, `deliberation`, `public_page` | panels inside core destinations (collapsed until enabled, T02) | `VotingPlan`, `MentorProfile`, `DeliberationRoom`, `Page` | |

Only the organizer/admin navigation changes in this batch. Participant, judge, mentor and volunteer destinations keep their static lists (limitation, follow-up F071).

**Readiness (T05), one rule registry.** `eventconfig/readiness.py` holds the only readiness rules: id, `severity` (`blocker|warning`), `module` (a disabled module contributes **no** rule), `passed`, a `Reason {code, message, fix:{destination, anchor}}` and whether it is checkable before launch. The 7 checklist rules and the 3 dashboard checks are migrated into it (ids preserved where they exist: `event_dates`, `forms_published`, `gate_windows`, `voting_window`, `judging_rubrics`, `judging_pools`, `public_page`; new: `tracks`, `base_prize`, `registration`). `compute_launch_checklist` and `configuration_checks` become **projections** of it (same response shapes, compatibility). Readiness stays **advisory** except `Event.clean` invariants: no new hard gate on `draft → open`; the open transition records the unresolved blocker/warning ids in its audit payload and returns the readiness snapshot. (A hard gate would change supported behavior for existing events and needs an owner decision; see the escalation.)

**Effective configuration API (T08).** `GET /workspaces/{w}/events/{e}/configuration/`, organizer/admin only, plain query parameters `module`, `tier`, `source`, `key` (no filter grammar; `QUERY` adopts these later). Each entry: `key`, `module`, `tier`, `label`, `type`, `value`, `default`, `baseline` (preset value), `source`, `editable` + `lock` reason, `write` (operation id), `derived_from`. Also `GET .../modules/` and `PATCH .../modules/{module}/` (audited `event.module_enabled|disabled`), `GET .../readiness/`. Created events record `preset_key/version` in the creation audit payload.

**Overrides (T07).** Every registry entry names the existing domain write and its `lock` rule (e.g. `registration.mode` locked once applications exist beyond its capability, dates locked by stage/submission windows via the existing serializers). The UI and automation read `editable/lock` from the registry and write through the domain endpoint, whose validation, audit and versioning are unchanged. A lock is a `Reason`, never a silent failure.

**Creation (T01/T03).** The Create-event flow asks at most: name, format (preset), start date + timezone, registration mode, team size range, visibility. Everything else is a real default from the preset: slug derived from name (editable), end date derived from the preset duration, registration row created, stage graph, tracks only when inherent to the format, evaluation plan with a **published** rubric (criteria from the preset), prize only when the preset defines one. Values that only the organizer knows (real dates, judges, prize amounts) are explicit readiness items, not placeholders.

### Primitive reuse decisions (required before implementation)

| Primitive | Status | Decision for this batch |
|---|---|---|
| `ROUTER` | exists in practice (PD-B04 `lib/routes.ts`, `Destination`, `useUrlParam`) | reuse directly; nav visibility and disabled-module deep links go through it; F071-B01 adopts, does not rebuild |
| `SCHEMA_EDITOR` | PLANNED (F002-B02-T01) | not built here. Registry `type` descriptors are JSON-Schema-compatible so it can consume them unchanged; UI uses the existing event-builder controls |
| `POLICY_EXPLAIN` | PLANNED (F002-B02-T06) | not built here. Lock and readiness reasons use one `Reason {code, message, fix}` shape owned by `eventconfig`; F002-B02-T06 must absorb it (obligation recorded in the escalation) |
| `QUERY` | PLANNED (F002-B01-T01) | not built here; plain query parameters only, no grammar |
| `ASYNC_JOB` | PLANNED (F002-B01-T05) | **not consumed**: preset application is one short atomic transaction; no job is created. Listed reuse recorded as not applicable |
| `RICH_DOC`, `APPROVAL` | PLANNED | not consumed in this batch (event description stays plain text; no approvals) |

**Forbidden:** a second settings/feature-flag table, a generic schema-form engine, a job runner, a filter grammar, a parallel readiness list, preset values duplicated outside `presets.py`, client-side enablement that is not derived from the server response, and treating hidden navigation as authorization (every endpoint keeps its own permission check).

### Compatibility and migration boundary

- Additive schema only (`EventProfile`, `EventModuleSetting`); no change to existing columns; legacy events need no backfill (no profile row = custom; effective modules derive from data).
- Unchanged response shapes: `EventDashboard.configuration_checks`, `communications/.../checklist/`, event template/library endpoints, event create. New fields are additive.
- Visible behavior change (intended): organizer navigation hides optional modules that are neither enabled nor in use. Browser specs that open a hidden destination (`integrations` on the reference event) assert that it is hidden and that its deep link explains; the integrations tour runs in `event-modules.spec.ts` after enabling it through the real UI (T04).
- New tables are excluded from the event archive with a recorded reason (`archive` not required); a cloned event re-derives `in_use` from cloned config rows, so only explicit "enabled but empty" intent is lost (limitation, revisited in S008).
- OpenAPI and SDKs regenerate (`sdk` surface: artifacts only, no new SDK capability).

### Task boundaries (this batch vs neighbours)

T01 guided create + preset catalog; T02 collapsed advanced panels; T03 real defaults (registration row, published rubric, derived dates/slug); T04 nav derived from effective modules; T05 canonical readiness; T06 `workflow_source` + switch to custom (detach is implicit: customizing flips `workflow_source`, nothing is reset); T07 `lock`/override contract through domain writes; T08 configuration API. **Not here:** weekend/online/internal formats, deadline editor, stage graph visualization, clone transfer choices (S007/S008), explicit-only generated config and consequence dialogs (F001-B02), participant/judge navigation.

### Verification strategy

Backend: unit tests per registry entry (default, baseline, source, lock), readiness rule table (passed/failed/disabled-module), projection tests proving the two legacy shapes are reproduced from the canonical rules, module enablement (enable, disable refused while in use, audit rows), preset application (all 5 formats produce no readiness blocker except organizer-only ones; unknown preset rejected; atomic rollback on failure), permission matrix (participant/judge/anonymous denied, cross-workspace denied). Compatibility: the census probe re-run shows 9/9 persisted events keep their data and the same legacy response bodies. Web: nav per effective modules, collapsed panels, deep link to a disabled module, create flow. Browser: seed-7 and fresh-fixture journeys; `make verify-fast`, `make e2e-fast`.
