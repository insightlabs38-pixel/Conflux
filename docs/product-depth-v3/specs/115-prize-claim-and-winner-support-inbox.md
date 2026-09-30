# PD-S115 — Prize claim and winner support inbox

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §115  
**Queue batches:** PD-S115-B01, PD-S115-B02

## Completion interpretation

This specification is the canonical depth contract for §115. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `ASYNC_JOB`
- `NOTIFICATIONS`
- `RICH_DOC`
- `SCHEMA_EDITOR`
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

Prize fulfillment can become a participant-friendly workflow.

- BASE — winner sees prize, status and required next action.
- BASE — secure contact/update form.
- ADV — required shipping/payment info fields determined by prize type.
- ADV — document request through external provider where sensitive.
- ADV — claim deadline.
- ADV — organizer/sponsor note.
- ADV — missing information reminder.
- ADV — support ticket linked to award.
- ADV — shipped/sent/claimed status.
- ADV — correction/alternate winner handling.
- SECURITY — minimize storage of sensitive financial/tax data; integrate rather than retain when possible.

**Why include:** Winning should not drop users into an email thread maze.

## Batch scope

### PD-S115-B01 — Prize claim and winner support inbox — winner sees prize, status and required… → support ticket linked to award

- winner sees prize, status and required next action
- secure contact/update form
- required shipping/payment info fields determined by prize type
- document request through external provider where sensitive
- claim deadline
- organizer/sponsor note
- missing information reminder
- support ticket linked to award

### PD-S115-B02 — Prize claim and winner support inbox — shipped/sent/claimed status → minimize storage of sensitive financial…

- shipped/sent/claimed status
- correction/alternate winner handling
- minimize storage of sensitive financial/tax data; integrate rather than retain when possible

