# PD-S073 — Personalized participant event pass / “My Event” hub

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §73  
**Queue batches:** PD-S073-B01, PD-S073-B02, PD-S073-B03, PD-S073-B04

## Completion interpretation

This specification is the canonical depth contract for §73. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- 'My Event' is a derived participant hub over canonical registration/team/project/submission/check-in/schedule state; it must not become another truth source.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `DATA_GRID`
- `POLICY_EXPLAIN`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
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
| `analytics` | not_required |
| `search` | required |
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

This is one of the most useful missing unification layers.

Instead of making a participant hunt through team, project, resources, schedule and check-in surfaces, provide one compact **My Event** page that answers:

- Am I accepted/confirmed?
- What do I need to do next?
- Who is on my team?
- What stage is my project in?
- When is the next deadline?
- What room/table am I assigned?
- What sessions did I RSVP to?
- What is my QR check-in pass?
- Which rules/waivers still need acknowledgement?
- Do I have unresolved eligibility findings?
- Do I have a mentor booking?
- When/where do I present?
- Has my submission finalized successfully?
- When will judging/results happen?
- Where are venue/travel instructions?

Useful depth:

- BASE — generated checklist ordered by urgency.
- BASE — exact next deadline with event/local timezone.
- BASE — QR event pass.
- BASE — team/project status.
- BASE — venue and check-in information.
- BASE — “you are ready” state when nothing remains.
- ADV — personalized schedule.
- ADV — meal/room/table/badge entitlements where enabled.
- ADV — travel/reimbursement status.
- ADV — accommodation request status.
- ADV — emergency/event contact.
- ADV — offline-friendly mobile version.
- ADV — wallet/pass export if easy to implement cleanly.
- PROG — hub is derived from canonical state; it should not introduce another workflow truth source.

**Why include:** It reduces navigation cost across almost every participant workflow and makes the large feature count feel simpler.

## Batch scope

### PD-S073-B01 — Personalized participant event pass / “My Event” hub — Participant hub must answer: Am I accep… → Participant hub must answer: What is my…

- Participant hub must answer: Am I accepted/confirmed?
- Participant hub must answer: What do I need to do next?
- Participant hub must answer: Who is on my team?
- Participant hub must answer: What stage is my project in?
- Participant hub must answer: When is the next deadline?
- Participant hub must answer: What room/table am I assigned?
- Participant hub must answer: What sessions did I RSVP to?
- Participant hub must answer: What is my QR check-in pass?

### PD-S073-B02 — Personalized participant event pass / “My Event” hub — Participant hub must answer: Which rule… → generated checklist ordered by urgency

- Participant hub must answer: Which rules/waivers still need acknowledgement?
- Participant hub must answer: Do I have unresolved eligibility findings?
- Participant hub must answer: Do I have a mentor booking?
- Participant hub must answer: When/where do I present?
- Participant hub must answer: Has my submission finalized successfully?
- Participant hub must answer: When will judging/results happen?
- Participant hub must answer: Where are venue/travel instructions?
- generated checklist ordered by urgency

### PD-S073-B03 — Personalized participant event pass / “My Event” hub — exact next deadline with event/local ti… → travel/reimbursement status

- exact next deadline with event/local timezone
- QR event pass
- team/project status
- venue and check-in information
- you are ready” state when nothing remains
- personalized schedule
- meal/room/table/badge entitlements where enabled
- travel/reimbursement status

### PD-S073-B04 — Personalized participant event pass / “My Event” hub — accommodation request status → hub is derived from canonical state; it…

- accommodation request status
- emergency/event contact
- offline-friendly mobile version
- wallet/pass export if easy to implement cleanly
- hub is derived from canonical state; it should not introduce another workflow truth source

