# PD-S087 — Travel, buses and reimbursement

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §87  
**Queue batches:** PD-S087-B01, PD-S087-B02

## Completion interpretation

This specification is the canonical depth contract for §87. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Travel support stops at event-specific instructions, shuttles and reimbursement workflow; booking/payment engines remain integrations.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `POLICY_EXPLAIN`
- `QUERY`
- `RICH_DOC`
- `ROUTER`
- `SCHEMA_EDITOR`

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
- No airline/hotel booking engine, payment processor or generic travel marketplace.

## Product requirements from research

This should be bounded and optional.

- BASE — event travel instructions and venue directions.
- BASE — parking/transit information.
- BASE — travel-assistance eligibility policy.
- ADV — attendee reimbursement request.
- ADV — amount/cap based on organizer rules.
- ADV — receipt upload.
- ADV — submitted/approved/paid/rejected status.
- ADV — organizer export to actual finance/payment system.
- ADV — bus/shuttle route and RSVP.
- ADV — seat capacity/waitlist.
- ADV — arrival/departure manifest for organizer.
- ADV — carpool interest as an opt-in discovery field; do not expose exact home addresses.
- ADV — hotel/accommodation instructions and externally managed booking reference.
- EXPERT — external finance provider integration for reimbursement payment.
- DO NOT BUILD — airline/hotel booking engine, payment processor, tax platform.

**Why include:** Hackathon software historically includes travel reimbursement and bus coordination; MLH has explicit travel/reimbursement guidance.

## Batch scope

### PD-S087-B01 — Travel, buses and reimbursement — event travel instructions and venue dir… → organizer export to actual finance/paym…

- event travel instructions and venue directions
- parking/transit information
- travel-assistance eligibility policy
- attendee reimbursement request
- amount/cap based on organizer rules
- receipt upload
- submitted/approved/paid/rejected status
- organizer export to actual finance/payment system

### PD-S087-B02 — Travel, buses and reimbursement — bus/shuttle route and RSVP → external finance provider integration f…

- bus/shuttle route and RSVP
- seat capacity/waitlist
- arrival/departure manifest for organizer
- carpool interest as an opt-in discovery field; do not expose exact home addresses
- hotel/accommodation instructions and externally managed booking reference
- external finance provider integration for reimbursement payment

