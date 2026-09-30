# PD-S120 — Event retrospective and next-edition handoff

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §120  
**Queue batches:** PD-S120-B01, PD-S120-B02

## Completion interpretation

This specification is the canonical depth contract for §120. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Retrospective aggregates verified operational evidence and human notes; any suggested next-edition changes are drafts, never automatic configuration mutation.

## Canonical primitive reuse

- `ASYNC_JOB`
- `RICH_DOC`
- `SCHEMA_EDITOR`

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

A practical closeout artifact.

- BASE — what worked / what failed / metrics.
- ADV — incidents and bottlenecks automatically linked.
- ADV — judge staffing actual vs plan.
- ADV — submission surge actual vs forecast.
- ADV — sponsor/mentor utilization.
- ADV — help-desk top categories.
- ADV — participant survey themes.
- ADV — unresolved tasks carried into next edition.
- ADV — recommended template/config updates as *drafts*, not auto-applied.
- ADV — create next-edition backlog.

**Why include:** Makes Conflux valuable between events, not just during one.

## Batch scope

### PD-S120-B01 — Event retrospective and next-edition handoff — what worked / what failed / metrics → unresolved tasks carried into next edit…

- what worked / what failed / metrics
- incidents and bottlenecks automatically linked
- judge staffing actual vs plan
- submission surge actual vs forecast
- sponsor/mentor utilization
- help-desk top categories
- participant survey themes
- unresolved tasks carried into next edition

### PD-S120-B02 — Event retrospective and next-edition handoff — recommended template/config updates as… → create next-edition backlog

- recommended template/config updates as *drafts*, not auto-applied
- create next-edition backlog

