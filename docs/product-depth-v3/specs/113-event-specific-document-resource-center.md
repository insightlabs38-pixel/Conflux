# PD-S113 — Event-specific document/resource center

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §113  
**Queue batches:** PD-S113-B01, PD-S113-B02

## Completion interpretation

This specification is the canonical depth contract for §113. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `RICH_DOC`
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
| `search` | required |
| `docs` | required |

## Approved-design references

- `design/participant-my-event`
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

Useful resources should not be scattered across FAQ, pages, sponsor blocks and messages.

- BASE — organized resources by category.
- BASE — visibility by role/stage.
- BASE — file/link/title/description.
- ADV — version/update timestamp.
- ADV — pin critical resources.
- ADV — acknowledgement requirement when appropriate.
- ADV — downloadable offline event pack.
- ADV — resource health/link checker.
- ADV — archive resources with event.
- ADV — per-track/sponsor resources.

**Why include:** Simplifies event resource discovery and naturally reuses page/resource primitives.

## Batch scope

### PD-S113-B01 — Event-specific document/resource center — organized resources by category → resource health/link checker

- organized resources by category
- visibility by role/stage
- file/link/title/description
- version/update timestamp
- pin critical resources
- acknowledgement requirement when appropriate
- downloadable offline event pack
- resource health/link checker

### PD-S113-B02 — Event-specific document/resource center — archive resources with event → per-track/sponsor resources

- archive resources with event
- per-track/sponsor resources

