# PD-S066 — Feedback and post-judging participant experience

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §66  
**Queue batches:** PD-S066-B01, PD-S066-B02

## Completion interpretation

This specification is the canonical depth contract for §66. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `AUDIT_PROVENANCE`
- `DATA_GRID`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `THREADS`
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
| `archive` | required |
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

Feedback release can become a thoughtful product, not a dump of judge comments.
- BASE — release judge feedback after configured time.
- BASE — organizer controls anonymous/named attribution.
- BASE — hide internal-only notes.
- ADV — criterion-level feedback.
- ADV — organizer redaction workflow preserving original internally.
- ADV — feedback quality checklist.
- ADV — participant acknowledge/read receipt.
- ADV — participant clarification question window.
- ADV — judge answer workflow.
- ADV — meta-review summary.
- ADV — downloadable feedback packet.
- EXPERT — review-quality rating by organizers or participants with guardrails.
- EXPERT — calibration analytics incorporate review-quality signals without silently changing official scores.
- PROG — feedback release uses immutable selected source versions.

## Batch scope

### PD-S066-B01 — Feedback and post-judging participant experience — release judge feedback after configured… → participant clarification question wind…

- release judge feedback after configured time
- organizer controls anonymous/named attribution
- hide internal-only notes
- criterion-level feedback
- organizer redaction workflow preserving original internally
- feedback quality checklist
- participant acknowledge/read receipt
- participant clarification question window

### PD-S066-B02 — Feedback and post-judging participant experience — judge answer workflow → feedback release uses immutable selecte…

- judge answer workflow
- meta-review summary
- downloadable feedback packet
- review-quality rating by organizers or participants with guardrails
- calibration analytics incorporate review-quality signals without silently changing official scores
- feedback release uses immutable selected source versions

