# PD-S026 — Pairwise judging and ranking

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §26  
**Queue batches:** PD-S026-B01, PD-S026-B02

## Completion interpretation

This specification is the canonical depth contract for §26. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Pairwise scheduling/ranking must surface disconnected or weak comparison graphs and never pretend convergence where evidence is insufficient.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `POLICY_EXPLAIN`
- `RICH_DOC`
- `SCHEMA_EDITOR`
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

Pairwise judging can become much more than a Bradley–Terry checkbox.
- BASE — fast A-vs-B decision UI.
- BASE — skip/recuse/tie policy.
- BASE — ranking generated from pairwise outcomes.
- ADV — adaptive pair selection maximizing information gain.
- ADV — avoid repeated same-judge/team interactions where possible.
- ADV — combine rubric and pairwise evidence.
- ADV — pairwise workload budget.
- ADV — ranking convergence/stability indicator.
- ADV — disconnected comparison graph diagnostics.
- ADV — suggest next comparisons to repair graph weakness.
- ADV — pairwise result sensitivity explorer.
- EXPERT — multiple ranking models available only through explicit configured method/version.
- EXPERT — uncertainty/stability analysis.
- EXPERT — active scheduling with judge expertise/COI constraints.
- EXPERT — audit graph showing which comparisons support a rank difference.
- PROG — deterministic schedule generation and replay.

## Batch scope

### PD-S026-B01 — Pairwise judging and ranking — fast A-vs-B decision UI → ranking convergence/stability indicator

- fast A-vs-B decision UI
- skip/recuse/tie policy
- ranking generated from pairwise outcomes
- adaptive pair selection maximizing information gain
- avoid repeated same-judge/team interactions where possible
- combine rubric and pairwise evidence
- pairwise workload budget
- ranking convergence/stability indicator

### PD-S026-B02 — Pairwise judging and ranking — disconnected comparison graph diagnosti… → deterministic schedule generation and r…

- disconnected comparison graph diagnostics
- suggest next comparisons to repair graph weakness
- pairwise result sensitivity explorer
- multiple ranking models available only through explicit configured method/version
- uncertainty/stability analysis
- active scheduling with judge expertise/COI constraints
- audit graph showing which comparisons support a rank difference
- deterministic schedule generation and replay

