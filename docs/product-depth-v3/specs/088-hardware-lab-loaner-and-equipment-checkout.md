# PD-S088 — Hardware lab, loaner and equipment checkout

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §88  
**Queue batches:** PD-S088-B01, PD-S088-B02

## Completion interpretation

This specification is the canonical depth contract for §88. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Equipment checkout is event inventory, not a general ERP. Safety/training requirements must block restricted checkout where configured.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `NOTIFICATIONS`
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
- No general asset-management/ERP scope.

## Product requirements from research

Especially valuable for hardware, robotics and sponsor-device events.

- BASE — inventory item/type and quantity.
- BASE — checkout/return to participant/team.
- BASE — item identifier/QR.
- BASE — current availability.
- ADV — reservation queue.
- ADV — item condition.
- ADV — due/return reminder.
- ADV — consumable vs returnable.
- ADV — restricted equipment requiring approved training.
- ADV — equipment location.
- ADV — missing/damaged status.
- ADV — per-team quota.
- ADV — sponsor-owned inventory.
- ADV — setup/tutorial linked to equipment.
- EXPERT — lab capacity/time-slot reservation for machines such as laser cutters/3D printers.
- EXPERT — safety acknowledgement before restricted tool use.
- DO NOT BUILD — general asset-management/ERP system.

**Why include:** Hardware resources are a real differentiator for physical events and fit naturally with sponsor resources, check-in and team state.

## Batch scope

### PD-S088-B01 — Hardware lab, loaner and equipment checkout — inventory item/type and quantity → consumable vs returnable

- inventory item/type and quantity
- checkout/return to participant/team
- item identifier/QR
- current availability
- reservation queue
- item condition
- due/return reminder
- consumable vs returnable

### PD-S088-B02 — Hardware lab, loaner and equipment checkout — restricted equipment requiring approved… → safety acknowledgement before restricte…

- restricted equipment requiring approved training
- equipment location
- missing/damaged status
- per-team quota
- sponsor-owned inventory
- setup/tutorial linked to equipment
- lab capacity/time-slot reservation for machines such as laser cutters/3D printers
- safety acknowledgement before restricted tool use

