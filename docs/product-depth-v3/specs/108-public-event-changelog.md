# PD-S108 — Public event changelog

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §108  
**Queue batches:** PD-S108-B01

## Completion interpretation

This specification is the canonical depth contract for §108. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `TIMELINE`
- `VERSION_DIFF`

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

A small transparency feature for events with evolving rules/schedule.

- BASE — important organizer changes can optionally be published as a changelog entry.
- BASE — date/time and summary.
- ADV — link to affected rule/schedule/page.
- ADV — “substantive” vs “minor wording” classification.
- ADV — participants can subscribe to changes.
- ADV — auto-draft from a semantic configuration diff.
- DO NOT BUILD — publish every internal audit event.

**Why include:** Participants care when rules/deadlines change, not about internal CRUD logs.

## Batch scope

### PD-S108-B01 — Public event changelog — important organizer changes can optiona… → auto-draft from a semantic configuratio…

- important organizer changes can optionally be published as a changelog entry
- date/time and summary
- link to affected rule/schedule/page
- substantive” vs “minor wording” classification
- participants can subscribe to changes
- auto-draft from a semantic configuration diff

