# PD-S082 — Help desk / organizer support queue

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §82  
**Queue batches:** PD-S082-B01, PD-S082-B02

## Completion interpretation

This specification is the canonical depth contract for §82. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Help desk is an operational queue, not a built-in Slack/Discord replacement.

## Canonical primitive reuse

- `ASYNC_JOB`
- `NOTIFICATIONS`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `THREADS`

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
| `search` | required |
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
- Do not build generic chat, voice rooms or community-server features.

## Product requirements from research

Mentor help and operational help are different.

- BASE — attendee can ask a logistics/event question.
- BASE — categories: registration, team, submission, venue, accessibility, technical platform, prize, other.
- BASE — triage/claim/resolve.
- BASE — participant sees status.
- ADV — priority/urgency.
- ADV — location/room.
- ADV — internal note vs participant-visible response.
- ADV — canned answers linked to FAQ.
- ADV — convert repeated issue into announcement/FAQ suggestion.
- ADV — handoff to mentor queue when question is actually technical.
- ADV — organizer SLA and backlog dashboard.
- ADV — Discord/Slack intake adapter if desired.
- EXPERT — outage/banner mode when many tickets share one incident.

**Why include:** This is a real event workflow and naturally reuses the mentor queue primitive.

## Batch scope

### PD-S082-B01 — Help desk / organizer support queue — attendee can ask a logistics/event ques… → canned answers linked to FAQ

- attendee can ask a logistics/event question
- categories: registration, team, submission, venue, accessibility, technical platform, prize, other
- triage/claim/resolve
- participant sees status
- priority/urgency
- location/room
- internal note vs participant-visible response
- canned answers linked to FAQ

### PD-S082-B02 — Help desk / organizer support queue — convert repeated issue into announcemen… → outage/banner mode when many tickets sh…

- convert repeated issue into announcement/FAQ suggestion
- handoff to mentor queue when question is actually technical
- organizer SLA and backlog dashboard
- Discord/Slack intake adapter if desired
- outage/banner mode when many tickets share one incident

