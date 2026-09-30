# PD-S109 — Participant-facing notification center with actionability

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §109  
**Queue batches:** PD-S109-B01, PD-S109-B02, PD-S109-B03

## Completion interpretation

This specification is the canonical depth contract for §109. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

## Canonical primitive reuse

- `APPROVAL`
- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `DATA_GRID`
- `NOTIFICATIONS`
- `POLICY_EXPLAIN`
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
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | required |
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

The first pass included notifications; this adds a stronger usefulness requirement.

Every notification should preferably answer:

- What happened?
- Does it require me to act?
- By when?
- Where do I act?
- Can it be safely dismissed?

Useful types:

- team invite;
- application decision;
- waitlist promotion;
- missing RSVP;
- rule acknowledgement;
- submission issue;
- eligibility remediation;
- mentor booking;
- room/table assignment;
- schedule/location change;
- judge assignment;
- feedback released;
- prize fulfillment action.

Avoid:

- noisy “someone viewed your project” activity;
- meaningless engagement gamification;
- duplicated email + banner + inbox messages with no preference controls.

## Batch scope

### PD-S109-B01 — Participant-facing notification center with actionability — Notification content contract: What hap… → Actionable notification: waitlist promo…

- Notification content contract: What happened?
- Notification content contract: Does it require me to act?
- Notification content contract: By when?
- Notification content contract: Where do I act?
- Notification content contract: Can it be safely dismissed?
- Actionable notification: team invite
- Actionable notification: application decision
- Actionable notification: waitlist promotion

### PD-S109-B02 — Participant-facing notification center with actionability — Actionable notification: missing RSVP → Actionable notification: judge assignme…

- Actionable notification: missing RSVP
- Actionable notification: rule acknowledgement
- Actionable notification: submission issue
- Actionable notification: eligibility remediation
- Actionable notification: mentor booking
- Actionable notification: room/table assignment
- Actionable notification: schedule/location change
- Actionable notification: judge assignment

### PD-S109-B03 — Participant-facing notification center with actionability — Actionable notification: feedback relea… → Actionable notification: prize fulfillm…

- Actionable notification: feedback released
- Actionable notification: prize fulfillment action

