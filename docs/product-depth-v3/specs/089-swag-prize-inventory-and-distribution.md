# PD-S089 — Swag, prize inventory and distribution

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §89  
**Queue batches:** PD-S089-B01, PD-S089-B02

## Completion interpretation

This specification is the canonical depth contract for §89. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `POLICY_EXPLAIN`
- `RICH_DOC`

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
| `search` | not_required |
| `docs` | required |

## Approved-design references

- `design/onsite-mobile`
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
- No warehouse-management system.

## Product requirements from research

Prizes already have fulfillment. The same simple inventory primitive can handle event materials.

- BASE — item, variant/size, stock.
- BASE — eligibility group.
- BASE — claimed/unclaimed.
- ADV — size preference at registration.
- ADV — QR/badge claim.
- ADV — prevent duplicate claim.
- ADV — low-stock warning.
- ADV — role-specific packs.
- ADV — sponsor swag allocation.
- ADV — leftover/undistributed count.
- ADV — winner physical prize handoff.
- ADV — shipping-needed flag for remote winners.
- EXPERT — external fulfillment/shipping integration.
- DO NOT BUILD — warehouse management.

**Why include:** Organizers repeatedly track shirts, stickers, packs and physical prizes manually.

## Batch scope

### PD-S089-B01 — Swag, prize inventory and distribution — item, variant/size, stock → role-specific packs

- item, variant/size, stock
- eligibility group
- claimed/unclaimed
- size preference at registration
- QR/badge claim
- prevent duplicate claim
- low-stock warning
- role-specific packs

### PD-S089-B02 — Swag, prize inventory and distribution — sponsor swag allocation → external fulfillment/shipping integrati…

- sponsor swag allocation
- leftover/undistributed count
- winner physical prize handoff
- shipping-needed flag for remote winners
- external fulfillment/shipping integration

