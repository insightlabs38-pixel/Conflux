# PD-S035 — Hybrid/in-person check-in and access control

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §35  
**Queue batches:** PD-S035-B01, PD-S035-B02, PD-S035-B03

## Completion interpretation

This specification is the canonical depth contract for §35. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `QUERY`
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

## Product requirements from research

pretix demonstrates how deep “check-in” can become. Conflux can take the relevant event-operations parts without turning into a ticketing platform.
- BASE — QR and manual lookup check-in.
- BASE — volunteer-scoped check-in permissions.
- BASE — check-in timestamp and operator/device.
- BASE — duplicate scan explanation.
- ADV — multiple independent check-in lists: event entrance, workshop, judging expo, meal, restricted room.
- ADV — list eligibility by role/track/status.
- ADV — check-out / re-entry.
- ADV — multiple-entry policy.
- ADV — gate/device identifiers.
- ADV — failed-scan logs with reason.
- ADV — participant badge lookup.
- ADV — badge printing on check-in.
- ADV — badge layout templates.
- ADV — attendance certificate trigger.
- ADV — offline scanner queue with nonce/idempotency and sync reconciliation.
- ADV — explicit stale-data warning in offline mode.
- EXPERT — access policy simulator.
- EXPERT — device enrollment/revocation.
- EXPERT — venue-wide live attendance occupancy by zone where configured.
- PROG — scanner API designed for untrusted scanned input and least privilege.

## Batch scope

### PD-S035-B01 — Hybrid/in-person check-in and access control — QR and manual lookup check-in → multiple-entry policy

- QR and manual lookup check-in
- volunteer-scoped check-in permissions
- check-in timestamp and operator/device
- duplicate scan explanation
- multiple independent check-in lists: event entrance, workshop, judging expo, meal, restricted room
- list eligibility by role/track/status
- check-out / re-entry
- multiple-entry policy

### PD-S035-B02 — Hybrid/in-person check-in and access control — gate/device identifiers → explicit stale-data warning in offline…

- gate/device identifiers
- failed-scan logs with reason
- participant badge lookup
- badge printing on check-in
- badge layout templates
- attendance certificate trigger
- offline scanner queue with nonce/idempotency and sync reconciliation
- explicit stale-data warning in offline mode

### PD-S035-B03 — Hybrid/in-person check-in and access control — access policy simulator → scanner API designed for untrusted scan…

- access policy simulator
- device enrollment/revocation
- venue-wide live attendance occupancy by zone where configured
- scanner API designed for untrusted scanned input and least privilege

