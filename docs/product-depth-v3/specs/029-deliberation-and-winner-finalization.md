# PD-S029 — Deliberation and winner finalization

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §29  
**Queue batches:** PD-S029-B01, PD-S029-B02, PD-S029-B03

## Completion interpretation

This specification is the canonical depth contract for §29. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Finalization is plan/approve/apply over frozen decision inputs. Overrides require attributable reasons and ordinary judges remain isolated from peer ballots.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `DATA_GRID`
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`
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
| `event_as_code` | required |
| `audit` | required |
| `webhook` | not_required |
| `archive` | required |
| `analytics` | not_required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- `design/deliberation-awards`
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

The final decision room should be one of Conflux's strongest differentiators.
- BASE — finalist table with scores, rank, coverage and warnings.
- BASE — side-by-side finalist comparison.
- BASE — award eligibility shown inline.
- BASE — immutable finalization receipt.
- ADV — criterion-by-criterion comparison.
- ADV — disagreement and close-call indicators.
- ADV — pairwise/rubric evidence tabs.
- ADV — deliberation notes with author/time.
- ADV — panel stances separate from ballots.
- ADV — recusal from deliberation.
- ADV — explicit override reason when final choice differs from configured ranking.
- ADV — decision approval threshold / required approvers.
- ADV — no-self-approval option.
- ADV — conflict solver across overlapping awards.
- ADV — preview public result before publish.
- EXPERT — deterministic “why A ranks over B” evidence graph.
- EXPERT — sensitivity report for finalists.
- EXPERT — freeze all decision inputs into portable audit capsule.
- PROG — finalization operation is plan/approve/apply, not an opaque write.

## Batch scope

### PD-S029-B01 — Deliberation and winner finalization — finalist table with scores, rank, cover… → deliberation notes with author/time

- finalist table with scores, rank, coverage and warnings
- side-by-side finalist comparison
- award eligibility shown inline
- immutable finalization receipt
- criterion-by-criterion comparison
- disagreement and close-call indicators
- pairwise/rubric evidence tabs
- deliberation notes with author/time

### PD-S029-B02 — Deliberation and winner finalization — panel stances separate from ballots → deterministic “why A ranks over B” evid…

- panel stances separate from ballots
- recusal from deliberation
- explicit override reason when final choice differs from configured ranking
- decision approval threshold / required approvers
- no-self-approval option
- conflict solver across overlapping awards
- preview public result before publish
- deterministic “why A ranks over B” evidence graph

### PD-S029-B03 — Deliberation and winner finalization — sensitivity report for finalists → finalization operation is plan/approve/…

- sensitivity report for finalists
- freeze all decision inputs into portable audit capsule
- finalization operation is plan/approve/apply, not an opaque write

