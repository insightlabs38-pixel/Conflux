# PD-S107 — Recurring event edition / year-over-year comparison

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §107  
**Queue batches:** PD-S107-B01, PD-S107-B02

## Completion interpretation

This specification is the canonical depth contract for §107. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Recurring editions inherit selectively; prior event history and judged artifacts remain separate rather than being overwritten.

## Canonical primitive reuse

- `ASYNC_JOB`
- `POLICY_EXPLAIN`
- `RICH_DOC`
- `SCHEMA_EDITOR`

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
| `archive` | required |
| `analytics` | required |
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

Conflux already has cloning and cross-event history; add a practical recurring-program workflow.

- BASE — “create next edition from this event.”
- BASE — explicit carry-over selection.
- BASE — preserved sponsor/judge/template references where appropriate.
- ADV — compare registration, attendance, submission and judging metrics across editions.
- ADV — compare sponsor challenge adoption.
- ADV — reused vs changed rules/rubrics.
- ADV — copy public pages as drafts with stale-date/link warnings.
- ADV — invite prior judges/mentors/participants selectively.
- ADV — prior-year project archive stays separate.
- EXPERT — organization program dashboard for a recurring series.

**Why include:** Repeat events are common, and recurring setup is where deep configuration can repay itself.

## Batch scope

### PD-S107-B01 — Recurring event edition / year-over-year comparison — create next edition from this event → invite prior judges/mentors/participant…

- create next edition from this event
- explicit carry-over selection
- preserved sponsor/judge/template references where appropriate
- compare registration, attendance, submission and judging metrics across editions
- compare sponsor challenge adoption
- reused vs changed rules/rubrics
- copy public pages as drafts with stale-date/link warnings
- invite prior judges/mentors/participants selectively

### PD-S107-B02 — Recurring event edition / year-over-year comparison — prior-year project archive stays separa… → organization program dashboard for a re…

- prior-year project archive stays separate
- organization program dashboard for a recurring series

