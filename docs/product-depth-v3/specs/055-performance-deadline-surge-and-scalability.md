# PD-S055 — Performance, deadline surge and scalability

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §55  
**Queue batches:** PD-S055-B01, PD-S055-B02, PD-S055-B03

## Completion interpretation

This specification is the canonical depth contract for §55. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Performance work is workload/SLO driven. Preserve integrity and correctness under load; do not optimize by weakening authoritative checks.

## Canonical primitive reuse

- `APPROVAL`
- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `NOTIFICATIONS`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `TIMELINE`
- `VERSION_DIFF`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | not_required |
| `api` | required |
| `sdk` | not_required |
| `cli` | not_required |
| `mcp` | not_required |
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | required |
| `archive` | not_required |
| `analytics` | required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- No dedicated visual reference is required by default. Any UI introduced still follows the global Conflux v3 design system.

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

The goal should be predictable behavior at deadline cliffs, not vanity aggregate RPS.
- BASE — publish workload-specific p50/p95/p99 for core flows.
- BASE — no integrity regression under load.
- ADV — scenarios for gallery browse, draft autosave, uploads, finalize, judging, voting, organizer dashboards and webhooks.
- ADV — connection-pool instrumentation.
- ADV — slow-query reporting.
- ADV — N+1 regression tests for high-volume endpoints.
- ADV — background expensive exports/reports.
- ADV — backpressure for organizer-heavy actions.
- ADV — cache only measured read hotspots.
- ADV — deadline finalization fast path that records durable intent/receipt before optional expensive follow-up.
- ADV — object-storage multipart/resume where large artifacts justify it.
- ADV — public static/cache strategy after publication.
- ADV — async fanout for messages/webhooks.
- EXPERT — synthetic event generator at 1k/10k/50k participants.
- EXPERT — chaos under load: worker restart, DB latency, object-store delay.
- EXPERT — capacity model based on event size and enabled features.
- EXPERT — automatic warning when configured deployment is below measured capacity envelope.
- PROG — performance evidence generated as versioned reports, not anecdotal claims.

## Batch scope

### PD-S055-B01 — Performance, deadline surge and scalability — publish workload-specific p50/p95/p99 f… → backpressure for organizer-heavy actions

- publish workload-specific p50/p95/p99 for core flows
- no integrity regression under load
- scenarios for gallery browse, draft autosave, uploads, finalize, judging, voting, organizer dashboards and webhooks
- connection-pool instrumentation
- slow-query reporting
- N+1 regression tests for high-volume endpoints
- background expensive exports/reports
- backpressure for organizer-heavy actions

### PD-S055-B02 — Performance, deadline surge and scalability — cache only measured read hotspots → capacity model based on event size and…

- cache only measured read hotspots
- deadline finalization fast path that records durable intent/receipt before optional expensive follow-up
- object-storage multipart/resume where large artifacts justify it
- public static/cache strategy after publication
- async fanout for messages/webhooks
- synthetic event generator at 1k/10k/50k participants
- chaos under load: worker restart, DB latency, object-store delay
- capacity model based on event size and enabled features

### PD-S055-B03 — Performance, deadline surge and scalability — automatic warning when configured deplo… → performance evidence generated as versi…

- automatic warning when configured deployment is below measured capacity envelope
- performance evidence generated as versioned reports, not anecdotal claims

