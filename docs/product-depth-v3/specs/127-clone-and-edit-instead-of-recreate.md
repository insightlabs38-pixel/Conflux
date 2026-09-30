# PD-S127 — Clone-and-edit instead of recreate

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §127  
**Queue batches:** PD-S127-B01, PD-S127-B02

## Completion interpretation

This specification is the canonical depth contract for §127. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

## Canonical primitive reuse

- `ASYNC_JOB`
- `NOTIFICATIONS`
- `POLICY_EXPLAIN`
- `QUERY`
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
| `event_as_code` | not_required |
| `audit` | not_required |
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

Apply consistently to:

- rubric;
- award;
- form;
- policy;
- communication;
- page;
- session;
- sponsor challenge;
- view;
- template;
- check-in list.

**Outcome:** repeated event configuration becomes much faster.

## Batch scope

### PD-S127-B01 — Clone-and-edit instead of recreate — Clone-and-edit: rubric → Clone-and-edit: sponsor challenge

- Clone-and-edit: rubric
- Clone-and-edit: award
- Clone-and-edit: form
- Clone-and-edit: policy
- Clone-and-edit: communication
- Clone-and-edit: page
- Clone-and-edit: session
- Clone-and-edit: sponsor challenge

### PD-S127-B02 — Clone-and-edit instead of recreate — Clone-and-edit: view → Clone-and-edit: check-in list

- Clone-and-edit: view
- Clone-and-edit: template
- Clone-and-edit: check-in list

