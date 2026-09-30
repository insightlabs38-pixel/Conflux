# PD-S067 — Moderation and trust/safety queues

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §67  
**Queue batches:** PD-S067-B01, PD-S067-B02

## Completion interpretation

This specification is the canonical depth contract for §67. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `AUDIT_PROVENANCE`
- `EXTENSION_MANIFEST`
- `POLICY_EXPLAIN`
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
| `archive` | not_required |
| `analytics` | not_required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- `design/organizer-data-surface`
- `design/public-project`
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

Community/public content requires a structured but proportionate moderation system.
- BASE — report project/comment/content.
- BASE — organizer moderation queue.
- BASE — hide/unhide with reason.
- ADV — category/severity.
- ADV — assignment to moderator.
- ADV — evidence snapshot at report time.
- ADV — participant appeal of moderation where event enables it.
- ADV — spam/rate signals.
- ADV — duplicate report grouping.
- ADV — action templates.
- ADV — public correction/reinstatement status when appropriate.
- EXPERT — extension hooks for external moderation scanners.
- EXPERT — audit separation between automated signal and human decision.
- PROG — moderation state is never conflated with judging/eligibility unless an explicit policy connects them.

## Batch scope

### PD-S067-B01 — Moderation and trust/safety queues — report project/comment/content → spam/rate signals

- report project/comment/content
- organizer moderation queue
- hide/unhide with reason
- category/severity
- assignment to moderator
- evidence snapshot at report time
- participant appeal of moderation where event enables it
- spam/rate signals

### PD-S067-B02 — Moderation and trust/safety queues — duplicate report grouping → moderation state is never conflated wit…

- duplicate report grouping
- action templates
- public correction/reinstatement status when appropriate
- extension hooks for external moderation scanners
- audit separation between automated signal and human decision
- moderation state is never conflated with judging/eligibility unless an explicit policy connects them

