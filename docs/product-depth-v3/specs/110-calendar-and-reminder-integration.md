# PD-S110 — Calendar and reminder integration

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §110  
**Queue batches:** PD-S110-B01, PD-S110-B02

## Completion interpretation

This specification is the canonical depth contract for §110. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `NOTIFICATIONS`
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

A practical cross-cutting feature.

- BASE — add event and key deadlines to calendar.
- BASE — event timezone embedded correctly.
- ADV — personal schedule iCalendar feed.
- ADV — judge assignment/calendar feed.
- ADV — mentor office-hours calendar.
- ADV — organizer run-of-show calendar.
- ADV — change/cancel updates propagate.
- ADV — configurable reminder preference.
- EXPERT — Google/Microsoft calendar integration only if needed beyond standards-based iCalendar.

**Why include:** Deadlines, sessions and judging windows are time-driven; calendar export is an expected convenience.

## Batch scope

### PD-S110-B01 — Calendar and reminder integration — add event and key deadlines to calendar → configurable reminder preference

- add event and key deadlines to calendar
- event timezone embedded correctly
- personal schedule iCalendar feed
- judge assignment/calendar feed
- mentor office-hours calendar
- organizer run-of-show calendar
- change/cancel updates propagate
- configurable reminder preference

### PD-S110-B02 — Calendar and reminder integration — Google/Microsoft calendar integration only if needed beyond stan…

- Google/Microsoft calendar integration only if needed beyond standards-based iCalendar

