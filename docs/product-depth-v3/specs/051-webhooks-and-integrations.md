# PD-S051 — Webhooks and integrations

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §51  
**Queue batches:** PD-S051-B01, PD-S051-B02, PD-S051-B03

## Completion interpretation

This specification is the canonical depth contract for §51. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `DATA_GRID`
- `EXTENSION_MANIFEST`
- `POLICY_EXPLAIN`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `TYPED_CLIENT`
- `VERSION_DIFF`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | required |
| `sdk` | required |
| `cli` | not_required |
| `mcp` | not_required |
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | required |
| `archive` | not_required |
| `analytics` | not_required |
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

The current signed/retrying webhook foundation can become an integration control plane.
- BASE — event types and delivery history.
- BASE — signing secret rotation.
- BASE — retry/backoff.
- BASE — manual replay.
- ADV — endpoint-level event filters.
- ADV — payload version pinning.
- ADV — test delivery with synthetic event.
- ADV — secret masking.
- ADV — disabled-after-repeated-failure policy.
- ADV — replay selected historical delivery.
- ADV — compare original/replayed payload.
- ADV — per-endpoint rate limits.
- ADV — dead-letter view.
- ADV — integration health dashboard.
- EXPERT — transform/filter step using constrained declarative mapping.
- EXPERT — inbound webhook adapters with signature verification.
- EXPERT — exactly-once impossible caveat handled via stable event IDs/idempotency.
- PROG — extension SDK can register integration type and UI config schema.

## Batch scope

### PD-S051-B01 — Webhooks and integrations — event types and delivery history → secret masking

- event types and delivery history
- signing secret rotation
- retry/backoff
- manual replay
- endpoint-level event filters
- payload version pinning
- test delivery with synthetic event
- secret masking

### PD-S051-B02 — Webhooks and integrations — disabled-after-repeated-failure policy → inbound webhook adapters with signature…

- disabled-after-repeated-failure policy
- replay selected historical delivery
- compare original/replayed payload
- per-endpoint rate limits
- dead-letter view
- integration health dashboard
- transform/filter step using constrained declarative mapping
- inbound webhook adapters with signature verification

### PD-S051-B03 — Webhooks and integrations — exactly-once impossible caveat handled… → extension SDK can register integration…

- exactly-once impossible caveat handled via stable event IDs/idempotency
- extension SDK can register integration type and UI config schema

