# PD-S022 — Rubric authoring and rubric laboratory

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §22  
**Queue batches:** PD-S022-B01, PD-S022-B02, PD-S022-B03

## Completion interpretation

This specification is the canonical depth contract for §22. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Published rubric versions remain immutable. Laboratory/simulation results must never silently alter official scoring configuration.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `DATA_GRID`
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`
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
| `event_as_code` | required |
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

Rubrics should be treated as versioned evaluation instruments rather than a list of weighted sliders.
- BASE — weighted criteria with descriptions and scale anchors.
- BASE — score validation and autosave.
- BASE — published rubric version becomes immutable.
- ADV — criterion groups and nested sections.
- ADV — explicit scale descriptors for each score band.
- ADV — optional/non-applicable criterion policy.
- ADV — rubric preview with example project.
- ADV — rubric version diff.
- ADV — weight-sum and scoring-distribution diagnostics.
- ADV — test rubric against historical/synthetic ballots.
- ADV — simulate effect of weight changes on historical ranking.
- ADV — identify criteria with low variance or weak discrimination.
- ADV — judge feedback on confusing criteria.
- ADV — calibration examples with reference reasoning.
- EXPERT — inter-criterion correlation diagnostics.
- EXPERT — sensitivity to normalization choices.
- EXPERT — rubric fairness/stability analysis without pretending statistics prove normative fairness.
- EXPERT — multiple rubric variants by track/stage with shared inherited criteria.
- PROG — rubric is portable/versioned configuration usable by replay.

## Batch scope

### PD-S022-B01 — Rubric authoring and rubric laboratory — weighted criteria with descriptions and… → rubric version diff

- weighted criteria with descriptions and scale anchors
- score validation and autosave
- published rubric version becomes immutable
- criterion groups and nested sections
- explicit scale descriptors for each score band
- optional/non-applicable criterion policy
- rubric preview with example project
- rubric version diff

### PD-S022-B02 — Rubric authoring and rubric laboratory — weight-sum and scoring-distribution dia… → sensitivity to normalization choices

- weight-sum and scoring-distribution diagnostics
- test rubric against historical/synthetic ballots
- simulate effect of weight changes on historical ranking
- identify criteria with low variance or weak discrimination
- judge feedback on confusing criteria
- calibration examples with reference reasoning
- inter-criterion correlation diagnostics
- sensitivity to normalization choices

### PD-S022-B03 — Rubric authoring and rubric laboratory — rubric fairness/stability analysis with… → rubric is portable/versioned configurat…

- rubric fairness/stability analysis without pretending statistics prove normative fairness
- multiple rubric variants by track/stage with shared inherited criteria
- rubric is portable/versioned configuration usable by replay

