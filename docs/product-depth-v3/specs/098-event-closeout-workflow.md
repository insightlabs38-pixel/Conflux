# PD-S098 — Event closeout workflow

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §98  
**Queue batches:** PD-S098-B01, PD-S098-B02

## Completion interpretation

This specification is the canonical depth contract for §98. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Closeout derives from canonical outstanding obligations and archives; closing event operations must not erase historical state.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `NOTIFICATIONS`
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`
- `RICH_DOC`
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
| `webhook` | required |
| `archive` | required |
| `analytics` | required |
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

Closing results is not the same as closing the event operationally.

- BASE — winners published.
- BASE — prizes/fulfillment outstanding.
- BASE — reimbursement outstanding.
- BASE — sponsor report outstanding.
- BASE — survey sent.
- BASE — volunteer/judge thank-you communications.
- BASE — archive/export complete.
- ADV — equipment returned.
- ADV — swag/prize leftovers accounted for.
- ADV — incident/helpdesk cases closed.
- ADV — post-event project continuation policy activated.
- ADV — static archive snapshot generated.
- ADV — event metrics frozen into final report.
- ADV — lessons/retrospective notes.
- ADV — clone-next-year action after closeout.
- EXPERT — generated closeout packet for partner organizations.

**Why include:** MLH explicitly treats event closeout as a separate workflow; Conflux has enough source data to make it automatic.

## Batch scope

### PD-S098-B01 — Event closeout workflow — winners published → equipment returned

- winners published
- prizes/fulfillment outstanding
- reimbursement outstanding
- sponsor report outstanding
- survey sent
- volunteer/judge thank-you communications
- archive/export complete
- equipment returned

### PD-S098-B02 — Event closeout workflow — swag/prize leftovers accounted for → generated closeout packet for partner o…

- swag/prize leftovers accounted for
- incident/helpdesk cases closed
- post-event project continuation policy activated
- static archive snapshot generated
- event metrics frozen into final report
- lessons/retrospective notes
- clone-next-year action after closeout
- generated closeout packet for partner organizations

