# PD-S106 — Event change impact and notification assistant

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §106  
**Queue batches:** PD-S106-B01

## Completion interpretation

This specification is the canonical depth contract for §106. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Impact analysis is dependency-driven and drafts suggested communication from structured changes; humans approve/send high-impact communication.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `NOTIFICATIONS`
- `PREVIEW_CONTEXT`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `TIMELINE`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | required |
| `sdk` | not_required |
| `cli` | not_required |
| `mcp` | not_required |
| `event_as_code` | required |
| `audit` | required |
| `webhook` | required |
| `archive` | not_required |
| `analytics` | not_required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- `design/event-builder`
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

When organizers change dates, rooms, requirements or rules, the system should identify affected people/workflows.

- BASE — configuration change preview says what operational state is impacted.
- ADV — identify participant cohorts affected by deadline/location/schedule change.
- ADV — suggest audience for notification.
- ADV — show existing scheduled communications that became stale.
- ADV — identify Event-as-Code docs/public pages that reference old value.
- ADV — require explicit acknowledgement for high-impact live-event change.
- ADV — create draft announcement from structured change facts; human edits/sends it.
- EXPERT — dependency graph across event config, pages, schedule, policies and integrations.

**Why include:** MLH explicitly emphasizes communicating major event changes quickly; Conflux has the domain data to automate the tedious impact discovery.

## Batch scope

### PD-S106-B01 — Event change impact and notification assistant — configuration change preview says what… → dependency graph across event config, p…

- configuration change preview says what operational state is impacted
- identify participant cohorts affected by deadline/location/schedule change
- suggest audience for notification
- show existing scheduled communications that became stale
- identify Event-as-Code docs/public pages that reference old value
- require explicit acknowledgement for high-impact live-event change
- create draft announcement from structured change facts; human edits/sends it
- dependency graph across event config, pages, schedule, policies and integrations

