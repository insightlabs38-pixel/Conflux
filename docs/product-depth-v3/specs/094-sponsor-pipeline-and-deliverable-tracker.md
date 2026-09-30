# PD-S094 — Sponsor pipeline and deliverable tracker

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §94  
**Queue batches:** PD-S094-B01, PD-S094-B02

## Completion interpretation

This specification is the canonical depth contract for §94. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Sponsor deliverables connect sponsorship promises to Conflux event state; CRM sales pipeline remains external.

## Canonical primitive reuse

- `ASYNC_JOB`
- `DATA_GRID`
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
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | required |
| `archive` | not_required |
| `analytics` | required |
| `search` | required |
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
- No full sales CRM pipeline.

## Product requirements from research

Conflux's sponsor resources/challenges begin after sponsorship exists. Organizers also need to ensure promised deliverables happen.

- BASE — sponsor organization/contact.
- BASE — sponsorship tier/package.
- BASE — committed cash/in-kind value.
- BASE — promised deliverables checklist.
- BASE — challenge/prize/resource links.
- ADV — logo/content deadline.
- ADV — workshop/office-hours slot.
- ADV — judge/mentor seats.
- ADV — booth/table placement.
- ADV — included announcement/email obligations.
- ADV — attendee data-sharing terms represented explicitly; never assumed.
- ADV — fulfillment owner/status.
- ADV — post-event sponsor report.
- ADV — renewal/follow-up reminder.
- EXPERT — import/export to external CRM instead of turning Conflux into Salesforce.
- DO NOT BUILD — full sales CRM pipeline unless later demand proves it belongs.

**Why include:** It connects sponsorship promises to actual event operations and sponsor ROI.

## Batch scope

### PD-S094-B01 — Sponsor pipeline and deliverable tracker — sponsor organization/contact → judge/mentor seats

- sponsor organization/contact
- sponsorship tier/package
- committed cash/in-kind value
- promised deliverables checklist
- challenge/prize/resource links
- logo/content deadline
- workshop/office-hours slot
- judge/mentor seats

### PD-S094-B02 — Sponsor pipeline and deliverable tracker — booth/table placement → import/export to external CRM instead o…

- booth/table placement
- included announcement/email obligations
- attendee data-sharing terms represented explicitly; never assumed
- fulfillment owner/status
- post-event sponsor report
- renewal/follow-up reminder
- import/export to external CRM instead of turning Conflux into Salesforce

