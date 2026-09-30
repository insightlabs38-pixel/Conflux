# PD-S103 — Contribution roles / team contribution record

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §103  
**Queue batches:** PD-S103-B01

## Completion interpretation

This specification is the canonical depth contract for §103. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `PREVIEW_CONTEXT`
- `QUERY`
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
| `webhook` | not_required |
| `archive` | not_required |
| `analytics` | not_required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- No dedicated visual reference is required by default. Any UI introduced still follows the global Conflux v3 design system.

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

Useful for judging and recruiting when participant-controlled.

- BASE — team members list roles/contributions.
- BASE — contribution statement frozen with submission.
- ADV — per-member technical/design/research/demo contributions.
- ADV — participant confirmation that team statement is accurate.
- ADV — organizer clarification if a prize is individual or role-restricted.
- EXPERT — repository contribution metadata can be shown only as supporting evidence; do not equate commit count with contribution quality.
- DO NOT BUILD — algorithmic “who really did the work” scoring.

**Why include:** Helps judges understand team composition and reduces ambiguity for prizes/recruiting.

## Batch scope

### PD-S103-B01 — Contribution roles / team contribution record — team members list roles/contributions → repository contribution metadata can be…

- team members list roles/contributions
- contribution statement frozen with submission
- per-member technical/design/research/demo contributions
- participant confirmation that team statement is accurate
- organizer clarification if a prize is individual or role-restricted
- repository contribution metadata can be shown only as supporting evidence; do not equate commit count with contribution quality

