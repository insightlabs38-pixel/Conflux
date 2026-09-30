# PD-S063 — Organizer operations center

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §63  
**Queue batches:** PD-S063-B01, PD-S063-B02

## Completion interpretation

This specification is the canonical depth contract for §63. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Operations dashboards link every metric/alert to actionable underlying records; avoid decorative dashboards disconnected from operations.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `POLICY_EXPLAIN`
- `QUERY`
- `RICH_DOC`
- `SAVED_VIEWS`
- `THREADS`
- `TIMELINE`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | required |
| `sdk` | not_required |
| `cli` | required |
| `mcp` | required |
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | required |
| `archive` | not_required |
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

The operations center should become a high-density command surface for live events.
- BASE — readiness, deadlines, active incidents and queues in one screen.
- BASE — participant/application/submission/judging counts.
- BASE — direct link from metric to filtered underlying records.
- ADV — customizable widgets from saved views.
- ADV — live judging completion.
- ADV — check-in/mentor/eligibility queue status.
- ADV — webhook/email/task failures.
- ADV — recent high-impact audit events.
- ADV — event timeline with next scheduled transitions.
- ADV — alert acknowledgment/assignment.
- ADV — incident note log.
- ADV — operations layout saved per user.
- EXPERT — big-screen operations layout.
- EXPERT — threshold/rule-driven alerts with cooldown.
- PROG — dashboard widgets use same query/metric definitions as analytics API.

## Batch scope

### PD-S063-B01 — Organizer operations center — readiness, deadlines, active incidents… → recent high-impact audit events

- readiness, deadlines, active incidents and queues in one screen
- participant/application/submission/judging counts
- direct link from metric to filtered underlying records
- customizable widgets from saved views
- live judging completion
- check-in/mentor/eligibility queue status
- webhook/email/task failures
- recent high-impact audit events

### PD-S063-B02 — Organizer operations center — event timeline with next scheduled tran… → dashboard widgets use same query/metric…

- event timeline with next scheduled transitions
- alert acknowledgment/assignment
- incident note log
- operations layout saved per user
- big-screen operations layout
- threshold/rule-driven alerts with cooldown
- dashboard widgets use same query/metric definitions as analytics API

