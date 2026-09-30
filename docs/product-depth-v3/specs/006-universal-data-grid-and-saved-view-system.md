# PD-F006 — Universal data-grid and saved-view system

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §6  
**Queue batches:** PD-F006-B01, PD-F006-B02, PD-F006-B03, PD-F006-B04, PD-F006-B05

## Completion interpretation

This specification is the canonical depth contract for §6. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Data grid, saved views and query/filtering must share one typed query model. URL state, saved state, bulk target selection, exports, CLI queries and MCP references must not fork into incompatible filter syntaxes.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `BULK_PLAN`
- `DATA_GRID`
- `PREVIEW_CONTEXT`
- `QUERY`
- `ROUTER`
- `SAVED_VIEWS`
- `SCHEMA_EDITOR`
- `TIMELINE`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | required |
| `sdk` | not_required |
| `cli` | required |
| `mcp` | required |
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | not_required |
| `archive` | not_required |
| `analytics` | not_required |
| `search` | required |
| `docs` | required |

## Approved-design references

- `design/organizer-data-surface`
- `design/state-matrix`

These references must resolve to approved local design artifacts before UI-facing tasks close.

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

This is one of the highest-leverage UI primitives.

- BASE: sortable columns.
- BASE: search.
- BASE: structured filters.
- BASE: row selection.
- BASE: bulk-action bar.
- BASE: column show/hide.
- BASE: pagination or virtualized windowing depending on dataset.
- BASE: sticky header where appropriate.
- BASE: responsive fallback for narrow screens.
- ADV: nested AND/OR filter groups.
- ADV: filter operators appropriate to data type.
- ADV: saved private views.
- ADV: shared organizer views.
- ADV: favorite/pin views.
- ADV: URL-encoded shareable transient views.
- ADV: group/subgroup.
- ADV: list / board / matrix / calendar where semantically valid.
- ADV: aggregate footer values.
- ADV: computed columns.
- ADV: inline editing with validation.
- ADV: keyboard row navigation and range selection.
- ADV: split-pane inspection.
- ADV: “only changed since…” filter.
- ADV: view templates.
- EXPERT: text query language equivalent to UI filters.
- EXPERT: organization-managed canonical views.
- EXPERT: permission-aware columns/filters.
- EXPERT: export the current exact filtered view.
- EXPERT: subscribe to view changes.
- PROG: saved-view schema is accessible over API.
- PROG: CLI can run the same query.
- PROG: MCP can reference a saved view rather than re-send a giant filter.
- PROG: bulk operations can consume a saved view with a frozen membership snapshot.

## Batch scope

### PD-F006-B01 — Universal data-grid and saved-view system — sortable columns → sticky header where appropriate

- sortable columns
- search
- structured filters
- row selection
- bulk-action bar
- column show/hide
- pagination or virtualized windowing depending on dataset
- sticky header where appropriate

### PD-F006-B02 — Universal data-grid and saved-view system — responsive fallback for narrow screens → group/subgroup

- responsive fallback for narrow screens
- nested AND/OR filter groups
- filter operators appropriate to data type
- saved private views
- shared organizer views
- favorite/pin views
- URL-encoded shareable transient views
- group/subgroup

### PD-F006-B03 — Universal data-grid and saved-view system — list / board / matrix / calendar where… → view templates

- list / board / matrix / calendar where semantically valid
- aggregate footer values
- computed columns
- inline editing with validation
- keyboard row navigation and range selection
- split-pane inspection
- only changed since…” filter
- view templates

### PD-F006-B04 — Universal data-grid and saved-view system — text query language equivalent to UI fi… → MCP can reference a saved view rather t…

- text query language equivalent to UI filters
- organization-managed canonical views
- permission-aware columns/filters
- export the current exact filtered view
- subscribe to view changes
- saved-view schema is accessible over API
- CLI can run the same query
- MCP can reference a saved view rather than re-send a giant filter

### PD-F006-B05 — Universal data-grid and saved-view system — bulk operations can consume a saved view with a frozen membershi…

- bulk operations can consume a saved view with a frozen membership snapshot

