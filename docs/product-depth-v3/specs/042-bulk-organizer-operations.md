# PD-S042 — Bulk organizer operations

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §42  
**Queue batches:** PD-S042-B01, PD-S042-B02

## Completion interpretation

This specification is the canonical depth contract for §42. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `AUDIT_PROVENANCE`
- `BULK_PLAN`
- `PREVIEW_CONTEXT`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `VERSION_DIFF`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | required |
| `sdk` | not_required |
| `cli` | required |
| `mcp` | required |
| `event_as_code` | required |
| `audit` | required |
| `webhook` | required |
| `archive` | not_required |
| `analytics` | required |
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

Bulk actions should be powerful precisely because they are safe and reviewable.
- BASE — select visible/filtered rows.
- BASE — clear recipient/object count.
- BASE — common safe bulk edits.
- ADV — operate on frozen saved-view membership.
- ADV — dry-run with per-object outcome.
- ADV — validation failures grouped before apply.
- ADV — conflict detection if objects change after preview.
- ADV — exact execution receipt.
- ADV — async execution for large sets.
- ADV — progress and cancellation where safe.
- ADV — retry failed subset.
- ADV — compensating rollback for reversible actions.
- ADV — approval requirement based on action/risk/size.
- EXPERT — import CSV assignment/action plan then dry-run atomically, similar to mature conference systems.
- EXPERT — operation templates.
- PROG — bulk planner is a general backend primitive reused by CLI/MCP.

## Batch scope

### PD-S042-B01 — Bulk organizer operations — select visible/filtered rows → exact execution receipt

- select visible/filtered rows
- clear recipient/object count
- common safe bulk edits
- operate on frozen saved-view membership
- dry-run with per-object outcome
- validation failures grouped before apply
- conflict detection if objects change after preview
- exact execution receipt

### PD-S042-B02 — Bulk organizer operations — async execution for large sets → bulk planner is a general backend primi…

- async execution for large sets
- progress and cancellation where safe
- retry failed subset
- compensating rollback for reversible actions
- approval requirement based on action/risk/size
- import CSV assignment/action plan then dry-run atomically, similar to mature conference systems
- operation templates
- bulk planner is a general backend primitive reused by CLI/MCP

