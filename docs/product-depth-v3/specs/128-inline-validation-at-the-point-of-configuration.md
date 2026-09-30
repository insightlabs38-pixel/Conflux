# PD-S128 — Inline validation at the point of configuration

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §128  
**Queue batches:** PD-S128-B01

## Completion interpretation

This specification is the canonical depth contract for §128. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Inline validation must come from the same server/domain rules where authoritative; frontend hints cannot become a divergent rules engine.

## Canonical primitive reuse

- `ASYNC_JOB`
- `NOTIFICATIONS`
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
| `webhook` | not_required |
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

Examples:

- impossible deadline order;
- award with no eligible scope;
- judge pool too small;
- contrast failure;
- empty communication audience;
- room capacity exceeded;
- form condition referencing nonexistent field;
- Event-as-Code unmanaged/prune hazard.

**Outcome:** errors are fixed where they are created rather than discovered at launch.

## Batch scope

### PD-S128-B01 — Inline validation at the point of configuration — Inline validation: impossible deadline… → Inline validation: Event-as-Code unmana…

- Inline validation: impossible deadline order
- Inline validation: award with no eligible scope
- Inline validation: judge pool too small
- Inline validation: contrast failure
- Inline validation: empty communication audience
- Inline validation: room capacity exceeded
- Inline validation: form condition referencing nonexistent field
- Inline validation: Event-as-Code unmanaged/prune hazard

