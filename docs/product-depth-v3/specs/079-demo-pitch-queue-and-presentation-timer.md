# PD-S079 — Demo/pitch queue and presentation timer

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §79  
**Queue batches:** PD-S079-B01, PD-S079-B02

## Completion interpretation

This specification is the canonical depth contract for §79. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `NOTIFICATIONS`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
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

## Product requirements from research

Many events have live pitches, finals or scheduled demos in addition to science-fair judging.

- BASE — create demo session/room.
- BASE — ordered team queue.
- BASE — visible current/next team.
- BASE — configurable presentation and Q&A timer.
- BASE — presenter “ready/not ready.”
- ADV — multiple parallel rooms.
- ADV — judge panel per room.
- ADV — delay/reorder controls.
- ADV — screen/projector display mode.
- ADV — participant mobile queue position.
- ADV — automatic “report to staging area” notification.
- ADV — no-show handling.
- ADV — recording/video link attached to presentation slot.
- ADV — finalist queue built directly from deliberation result.
- EXPERT — room balancing from projected duration and judge availability.

**Why include:** It replaces the common spreadsheet + stopwatch + Discord message workflow.

## Batch scope

### PD-S079-B01 — Demo/pitch queue and presentation timer — create demo session/room → delay/reorder controls

- create demo session/room
- ordered team queue
- visible current/next team
- configurable presentation and Q&A timer
- presenter “ready/not ready
- multiple parallel rooms
- judge panel per room
- delay/reorder controls

### PD-S079-B02 — Demo/pitch queue and presentation timer — screen/projector display mode → room balancing from projected duration…

- screen/projector display mode
- participant mobile queue position
- automatic “report to staging area” notification
- no-show handling
- recording/video link attached to presentation slot
- finalist queue built directly from deliberation result
- room balancing from projected duration and judge availability

