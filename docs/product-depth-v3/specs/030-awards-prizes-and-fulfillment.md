# PD-S030 — Awards, prizes and fulfillment

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §30  
**Queue batches:** PD-S030-B01, PD-S030-B02, PD-S030-B03

## Completion interpretation

This specification is the canonical depth contract for §30. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Award allocation and fulfillment are separate state machines. Solver output is advisory/planned until an authorized finalization step.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `THREADS`
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
| `archive` | required |
| `analytics` | required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- `design/deliberation-awards`
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

Awards should model both selection logic and real fulfillment.
- BASE — cash/credit/physical/other typed prize.
- BASE — track/sponsor/global awards.
- BASE — winner count and eligibility.
- BASE — publication controls.
- ADV — composite award criteria.
- ADV — sponsor-specific judge pools.
- ADV — no-double-win / max-awards-per-project policies.
- ADV — award precedence and conflict resolution.
- ADV — honorable mentions.
- ADV — team-member-level entitlement splitting.
- ADV — fulfillment status: pending/contacted/verified/sent/claimed/expired.
- ADV — winner contact workflow.
- ADV — sponsor fulfillment export.
- ADV — tax/form/document checklist as configurable metadata, not legal advice.
- ADV — claim deadline and fallback winner workflow.
- EXPERT — optimization solver for award allocation under constraints.
- EXPERT — what-if allocation preview.
- EXPERT — signed award decision/fulfillment receipts.
- PROG — award configuration and allocation evidence export cleanly.

## Batch scope

### PD-S030-B01 — Awards, prizes and fulfillment — cash/credit/physical/other typed prize → award precedence and conflict resolution

- cash/credit/physical/other typed prize
- track/sponsor/global awards
- winner count and eligibility
- publication controls
- composite award criteria
- sponsor-specific judge pools
- no-double-win / max-awards-per-project policies
- award precedence and conflict resolution

### PD-S030-B02 — Awards, prizes and fulfillment — honorable mentions → optimization solver for award allocatio…

- honorable mentions
- team-member-level entitlement splitting
- fulfillment status: pending/contacted/verified/sent/claimed/expired
- winner contact workflow
- sponsor fulfillment export
- tax/form/document checklist as configurable metadata, not legal advice
- claim deadline and fallback winner workflow
- optimization solver for award allocation under constraints

### PD-S030-B03 — Awards, prizes and fulfillment — what-if allocation preview → award configuration and allocation evid…

- what-if allocation preview
- signed award decision/fulfillment receipts
- award configuration and allocation evidence export cleanly

