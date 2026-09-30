# PD-S036 — Floorplans, booths, rooms and spatial logistics

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §36  
**Queue batches:** PD-S036-B01, PD-S036-B02, PD-S036-B03

## Completion interpretation

This specification is the canonical depth contract for §36. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `DATA_GRID`
- `POLICY_EXPLAIN`
- `RICH_DOC`
- `ROUTER`

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

On-site logistics are already present; depth can turn them into a genuine operations system.
- BASE — assign project to table/booth/room.
- BASE — printable fallback layout.
- BASE — judge route over assigned projects.
- ADV — visual floorplan editor.
- ADV — zones and room capacities.
- ADV — accessibility constraints.
- ADV — power/network/special-equipment attributes.
- ADV — sponsor/track grouping preferences.
- ADV — adjacency constraints/preferences.
- ADV — automatic placement with hard/soft constraints.
- ADV — move/drag placement with immediate conflict diagnostics.
- ADV — QR table signage.
- ADV — participant-facing booth location.
- ADV — judge mobile route with completed/next stops.
- ADV — live reassignment after no-show.
- EXPERT — walking-time matrix / route optimization.
- EXPERT — infeasibility diagnosis explaining which constraints conflict.
- EXPERT — congestion-aware routing as an optional advanced model.
- PROG — floorplan/layout export to portable geometry JSON and print renderer.

## Batch scope

### PD-S036-B01 — Floorplans, booths, rooms and spatial logistics — assign project to table/booth/room → sponsor/track grouping preferences

- assign project to table/booth/room
- printable fallback layout
- judge route over assigned projects
- visual floorplan editor
- zones and room capacities
- accessibility constraints
- power/network/special-equipment attributes
- sponsor/track grouping preferences

### PD-S036-B02 — Floorplans, booths, rooms and spatial logistics — adjacency constraints/preferences → walking-time matrix / route optimization

- adjacency constraints/preferences
- automatic placement with hard/soft constraints
- move/drag placement with immediate conflict diagnostics
- QR table signage
- participant-facing booth location
- judge mobile route with completed/next stops
- live reassignment after no-show
- walking-time matrix / route optimization

### PD-S036-B03 — Floorplans, booths, rooms and spatial logistics — infeasibility diagnosis explaining whic… → floorplan/layout export to portable geo…

- infeasibility diagnosis explaining which constraints conflict
- congestion-aware routing as an optional advanced model
- floorplan/layout export to portable geometry JSON and print renderer

