# PD-S093 — Budget, sponsor commitments and event expenses — deliberately narrow scope

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §93  
**Queue batches:** PD-S093-B01, PD-S093-B02

## Completion interpretation

This specification is the canonical depth contract for §93. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Budget is lightweight event planning/commitment/expense tracking; no double-entry accounting, bank reconciliation, payroll or tax filing.

## Canonical primitive reuse

- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `RICH_DOC`

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
- No double-entry accounting, bank reconciliation, payroll or tax preparation.

## Product requirements from research

A lightweight event budget can remove a major spreadsheet without becoming accounting software.

- BASE — planned budget categories.
- BASE — committed vs actual.
- BASE — sponsor cash/in-kind commitments.
- BASE — event expenses.
- BASE — receipt/document attachment.
- ADV — vendor/expense status: planned/ordered/invoiced/paid.
- ADV — reimbursement linkage.
- ADV — sponsor commitment due date.
- ADV — per-attendee cost.
- ADV — budget variance.
- ADV — category export.
- ADV — read-only finance role.
- EXPERT — accounting/payment integrations via export/API.
- DO NOT BUILD — double-entry accounting, payroll, bank reconciliation, tax preparation.

**Why include:** Every hackathon has a budget, and MLH's own organizer model treats finance as a core organizing function.

## Batch scope

### PD-S093-B01 — Budget, sponsor commitments and event expenses — deliberately narrow scope — planned budget categories → sponsor commitment due date

- planned budget categories
- committed vs actual
- sponsor cash/in-kind commitments
- event expenses
- receipt/document attachment
- vendor/expense status: planned/ordered/invoiced/paid
- reimbursement linkage
- sponsor commitment due date

### PD-S093-B02 — Budget, sponsor commitments and event expenses — deliberately narrow scope — per-attendee cost → accounting/payment integrations via exp…

- per-attendee cost
- budget variance
- category export
- read-only finance role
- accounting/payment integrations via export/API

