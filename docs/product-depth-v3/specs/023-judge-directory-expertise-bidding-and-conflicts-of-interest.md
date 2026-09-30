# PD-S023 — Judge directory, expertise, bidding and conflicts of interest

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §23  
**Queue batches:** PD-S023-B01, PD-S023-B02, PD-S023-B03

## Completion interpretation

This specification is the canonical depth contract for §23. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Judge expertise, capacity, bids and conflicts have one canonical representation reused by staffing, assignment, routing and readiness.

## Canonical primitive reuse

- `ASYNC_JOB`
- `BULK_PLAN`
- `POLICY_EXPLAIN`
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
| `cli` | not_required |
| `mcp` | not_required |
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | not_required |
| `archive` | required |
| `analytics` | required |
| `search` | required |
| `docs` | required |

## Approved-design references

- `design/judge-review`
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

OpenReview-level assignment sophistication is a useful ceiling for Conflux's judging system.
- BASE — judge profile, capacity and availability.
- BASE — explicit conflicts/recusal.
- BASE — organizer-visible assignment progress.
- ADV — expertise taxonomy and proficiency.
- ADV — track preferences.
- ADV — project/topic bids: strong interest → no preference → avoid.
- ADV — max/min assignment preferences.
- ADV — availability windows for in-person judging.
- ADV — language constraints.
- ADV — declared organization/employment/mentor relationships.
- ADV — conflict policy with reason categories and visibility controls.
- ADV — organizer can add administrative conflict with reason.
- ADV — imported historical judge performance/load data.
- ADV — bulk judge import/update.
- ADV — reusable cross-event judge directory.
- EXPERT — computed affinity score from tags/text embeddings as an optional advisory signal.
- EXPERT — affinity explanation and manual override.
- EXPERT — conflict detection from declared relationships/history where data is available and consented.
- EXPERT — conflict policy year windows / relationship classes.
- EXPERT — judge reliability/calibration history used carefully as an assignment feature.
- PROG — judge constraints are structured inputs to assignment solver and replay.

## Batch scope

### PD-S023-B01 — Judge directory, expertise, bidding and conflicts of interest — judge profile, capacity and availability → availability windows for in-person judg…

- judge profile, capacity and availability
- explicit conflicts/recusal
- organizer-visible assignment progress
- expertise taxonomy and proficiency
- track preferences
- project/topic bids: strong interest → no preference → avoid
- max/min assignment preferences
- availability windows for in-person judging

### PD-S023-B02 — Judge directory, expertise, bidding and conflicts of interest — language constraints → computed affinity score from tags/text…

- language constraints
- declared organization/employment/mentor relationships
- conflict policy with reason categories and visibility controls
- organizer can add administrative conflict with reason
- imported historical judge performance/load data
- bulk judge import/update
- reusable cross-event judge directory
- computed affinity score from tags/text embeddings as an optional advisory signal

### PD-S023-B03 — Judge directory, expertise, bidding and conflicts of interest — affinity explanation and manual override → judge constraints are structured inputs…

- affinity explanation and manual override
- conflict detection from declared relationships/history where data is available and consented
- conflict policy year windows / relationship classes
- judge reliability/calibration history used carefully as an assignment feature
- judge constraints are structured inputs to assignment solver and replay

