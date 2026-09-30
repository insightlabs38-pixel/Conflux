# PD-S037 — Schedule, sessions, workshops and livestreams

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §37  
**Queue batches:** PD-S037-B01, PD-S037-B02, PD-S037-B03

## Completion interpretation

This specification is the canonical depth contract for §37. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `QUERY`
- `RICH_DOC`
- `TIMELINE`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | required |
| `sdk` | not_required |
| `cli` | not_required |
| `mcp` | not_required |
| `event_as_code` | required |
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

A hackathon schedule should be more than static text.
- BASE — sessions with time/location/title/speaker.
- BASE — timezone-aware public schedule.
- BASE — calendar export.
- ADV — tracks/rooms.
- ADV — RSVP/capacity.
- ADV — waiting list for limited session.
- ADV — livestream/recording link.
- ADV — session resources/slides.
- ADV — speaker profiles.
- ADV — participant personal schedule.
- ADV — reminders.
- ADV — cancellation/location-change push.
- ADV — session check-in.
- ADV — mentor/sponsor workshop linkage.
- EXPERT — schedule conflict detector.
- EXPERT — room capacity and equipment constraints.
- EXPERT — automatic schedule proposal from constraints.
- PROG — iCalendar/API/webhook representation.

## Batch scope

### PD-S037-B01 — Schedule, sessions, workshops and livestreams — sessions with time/location/title/speak… → session resources/slides

- sessions with time/location/title/speaker
- timezone-aware public schedule
- calendar export
- tracks/rooms
- RSVP/capacity
- waiting list for limited session
- livestream/recording link
- session resources/slides

### PD-S037-B02 — Schedule, sessions, workshops and livestreams — speaker profiles → room capacity and equipment constraints

- speaker profiles
- participant personal schedule
- reminders
- cancellation/location-change push
- session check-in
- mentor/sponsor workshop linkage
- schedule conflict detector
- room capacity and equipment constraints

### PD-S037-B03 — Schedule, sessions, workshops and livestreams — automatic schedule proposal from constr… → iCalendar/API/webhook representation

- automatic schedule proposal from constraints
- iCalendar/API/webhook representation

