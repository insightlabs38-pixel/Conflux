# PD-S033 — Mentorship, support requests and office hours

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §33  
**Queue batches:** PD-S033-B01, PD-S033-B02, PD-S033-B03

## Completion interpretation

This specification is the canonical depth contract for §33. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `NOTIFICATIONS`
- `RICH_DOC`
- `THREADS`
- `TIMELINE`
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
| `analytics` | required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- `design/event-builder`
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

Mentorship can become an operations queue optimized for getting teams unstuck.
- BASE — request help with topic/urgency.
- BASE — mentor expertise and availability.
- BASE — claim/reassign/resolve.
- BASE — participant-visible status.
- BASE — office-hours slots.
- ADV — triage categories.
- ADV — estimated wait time from queue state, clearly approximate.
- ADV — match by expertise/location/language.
- ADV — team can close/cancel request.
- ADV — mentor private note vs participant-visible resolution note.
- ADV — request history by team.
- ADV — organizer SLA/queue dashboard.
- ADV — on-site room/table assignment.
- ADV — calendar integration.
- ADV — follow-up rating.
- EXPERT — dispatch optimization under load.
- EXPERT — repeat-problem analytics that feed event FAQ/announcements.
- PROG — integrations can create/resolve requests from Discord/Slack without creating a competing chat product.

## Batch scope

### PD-S033-B01 — Mentorship, support requests and office hours — request help with topic/urgency → match by expertise/location/language

- request help with topic/urgency
- mentor expertise and availability
- claim/reassign/resolve
- participant-visible status
- office-hours slots
- triage categories
- estimated wait time from queue state, clearly approximate
- match by expertise/location/language

### PD-S033-B02 — Mentorship, support requests and office hours — team can close/cancel request → dispatch optimization under load

- team can close/cancel request
- mentor private note vs participant-visible resolution note
- request history by team
- organizer SLA/queue dashboard
- on-site room/table assignment
- calendar integration
- follow-up rating
- dispatch optimization under load

### PD-S033-B03 — Mentorship, support requests and office hours — repeat-problem analytics that feed even… → integrations can create/resolve request…

- repeat-problem analytics that feed event FAQ/announcements
- integrations can create/resolve requests from Discord/Slack without creating a competing chat product

