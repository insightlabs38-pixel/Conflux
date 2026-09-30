# PD-S024 — Judge assignment optimization

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §24  
**Queue batches:** PD-S024-B01, PD-S024-B02, PD-S024-B03

## Completion interpretation

This specification is the canonical depth contract for §24. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Assignment optimization separates hard constraints from soft objectives, is reproducible for fixed inputs/seed, and produces infeasibility diagnostics rather than silently weakening constraints.

## Canonical primitive reuse

- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `POLICY_EXPLAIN`
- `QUERY`
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

Assignment is already a technical strength. It can become an operator-grade optimization laboratory.
- BASE — satisfy conflicts, capacity and required coverage.
- BASE — deterministic output for same inputs/seed.
- BASE — clear infeasibility errors.
- ADV — expertise affinity objective.
- ADV — bid preference objective.
- ADV — balanced workload.
- ADV — cross-judge overlap/connectivity objective for normalization.
- ADV — track/language/time-window constraints.
- ADV — locked/manual assignments respected.
- ADV — multiple candidate assignment plans.
- ADV — plan quality metrics.
- ADV — before/apply diff.
- ADV — organizer modifications followed by re-optimization of remainder.
- ADV — alternate/backup judge list.
- ADV — judge dropout simulation.
- ADV — project-demand overrides.
- EXPERT — configurable lexicographic hard/soft objectives.
- EXPERT — min-max, fair-flow and alternative solver strategies where useful.
- EXPERT — Pareto-style comparison of competing assignment objectives.
- EXPERT — solver reproducibility capsule with inputs/version/seed.
- EXPERT — stability analysis: how much does solution change if one judge drops?
- EXPERT — assignment recommendation explanation per judge/project.
- PROG — `plan`, `apply`, `revert-to-plan`, and saved assignment snapshots.

## Batch scope

### PD-S024-B01 — Judge assignment optimization — satisfy conflicts, capacity and require… → track/language/time-window constraints

- satisfy conflicts, capacity and required coverage
- deterministic output for same inputs/seed
- clear infeasibility errors
- expertise affinity objective
- bid preference objective
- balanced workload
- cross-judge overlap/connectivity objective for normalization
- track/language/time-window constraints

### PD-S024-B02 — Judge assignment optimization — locked/manual assignments respected → project-demand overrides

- locked/manual assignments respected
- multiple candidate assignment plans
- plan quality metrics
- before/apply diff
- organizer modifications followed by re-optimization of remainder
- alternate/backup judge list
- judge dropout simulation
- project-demand overrides

### PD-S024-B03 — Judge assignment optimization — configurable lexicographic hard/soft ob… → plan, apply, revert-to-plan, and saved…

- configurable lexicographic hard/soft objectives
- min-max, fair-flow and alternative solver strategies where useful
- Pareto-style comparison of competing assignment objectives
- solver reproducibility capsule with inputs/version/seed
- stability analysis: how much does solution change if one judge drops?
- assignment recommendation explanation per judge/project
- `plan`, `apply`, `revert-to-plan`, and saved assignment snapshots

