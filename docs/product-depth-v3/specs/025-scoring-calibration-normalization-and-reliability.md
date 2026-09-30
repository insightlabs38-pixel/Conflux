# PD-S025 — Scoring, calibration, normalization and reliability

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §25  
**Queue batches:** PD-S025-B01, PD-S025-B02, PD-S025-B03

## Completion interpretation

This specification is the canonical depth contract for §25. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Normalization/calibration methods are explicit versioned methods. Derived official scores carry source ballot/rubric/method versions and are replayable.

## Canonical primitive reuse

- `ASYNC_JOB`
- `POLICY_EXPLAIN`
- `RICH_DOC`
- `SCHEMA_EDITOR`
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
| `analytics` | required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- `design/judge-review`
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

## Product requirements from research

This area can remain statistically sophisticated while being unusually transparent to organizers.
- BASE — raw rubric totals.
- BASE — normalized scores where configured.
- BASE — organizer explanation of normalization method.
- ADV — calibration round before live judging.
- ADV — reference projects/ballots.
- ADV — per-judge mean/variance and score-distribution diagnostics.
- ADV — inter-rater agreement metrics with appropriate caveats.
- ADV — criterion-level disagreement.
- ADV — outlier review queue.
- ADV — missing-score and partial-ballot policy.
- ADV — confidence field separate from score.
- ADV — compare raw vs normalized ranking.
- ADV — sensitivity to inclusion/exclusion of individual ballot.
- EXPERT — alternate defensible normalization models in a laboratory, never silently changed.
- EXPERT — judge-bias/model residual diagnostics.
- EXPERT — uncertainty intervals / bootstrap stability where assumptions support them.
- EXPERT — calibration drift over time.
- EXPERT — explicit model-version pinning and deterministic replay.
- PROG — every derived result carries source ballot/rubric/method versions.

## Batch scope

### PD-S025-B01 — Scoring, calibration, normalization and reliability — raw rubric totals → criterion-level disagreement

- raw rubric totals
- normalized scores where configured
- organizer explanation of normalization method
- calibration round before live judging
- reference projects/ballots
- per-judge mean/variance and score-distribution diagnostics
- inter-rater agreement metrics with appropriate caveats
- criterion-level disagreement

### PD-S025-B02 — Scoring, calibration, normalization and reliability — outlier review queue → uncertainty intervals / bootstrap stabi…

- outlier review queue
- missing-score and partial-ballot policy
- confidence field separate from score
- compare raw vs normalized ranking
- sensitivity to inclusion/exclusion of individual ballot
- alternate defensible normalization models in a laboratory, never silently changed
- judge-bias/model residual diagnostics
- uncertainty intervals / bootstrap stability where assumptions support them

### PD-S025-B03 — Scoring, calibration, normalization and reliability — calibration drift over time → every derived result carries source bal…

- calibration drift over time
- explicit model-version pinning and deterministic replay
- every derived result carries source ballot/rubric/method versions

