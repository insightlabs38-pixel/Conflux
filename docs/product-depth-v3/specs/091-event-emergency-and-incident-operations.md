# PD-S091 — Event emergency and incident operations

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §91  
**Queue batches:** PD-S091-B01, PD-S091-B02

## Completion interpretation

This specification is the canonical depth contract for §91. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Emergency operations support runbooks, communications and event-state impact; Conflux is not an emergency dispatch or medical-record system.

## Canonical primitive reuse

- `ASYNC_JOB`
- `DATA_GRID`
- `NOTIFICATIONS`
- `RICH_DOC`
- `THREADS`
- `TIMELINE`

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
- No emergency-dispatch or medical-record system.

## Product requirements from research

Separate emergency operations from Code-of-Conduct case management.

- BASE — emergency contact/runbook page for staff.
- BASE — venue emergency instructions.
- BASE — organizer “critical announcement” channel.
- ADV — incident type: medical, fire/alarm, weather, building, network/power, security, other.
- ADV — incident commander/owner.
- ADV — staff-only timeline.
- ADV — impacted rooms/sessions.
- ADV — attach emergency procedure.
- ADV — trigger public/role-scoped announcement with explicit human confirmation.
- ADV — post-incident notes.
- EXPERT — offline printable/exportable emergency pack.
- DO NOT BUILD — emergency dispatch or medical record system.

**Why include:** Emergency planning is ordinary live-event responsibility; Conflux already has communications and onsite state to make it useful.

## Batch scope

### PD-S091-B01 — Event emergency and incident operations — emergency contact/runbook page for staff → attach emergency procedure

- emergency contact/runbook page for staff
- venue emergency instructions
- organizer “critical announcement” channel
- incident type: medical, fire/alarm, weather, building, network/power, security, other
- incident commander/owner
- staff-only timeline
- impacted rooms/sessions
- attach emergency procedure

### PD-S091-B02 — Event emergency and incident operations — trigger public/role-scoped announcement… → offline printable/exportable emergency…

- trigger public/role-scoped announcement with explicit human confirmation
- post-incident notes
- offline printable/exportable emergency pack

