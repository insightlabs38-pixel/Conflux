# PD-S062 — Optional automated-evaluation competition modes

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §62  
**Queue batches:** PD-S062-B01, PD-S062-B02

## Completion interpretation

This specification is the canonical depth contract for §62. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `EXTENSION_MANIFEST`
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
- Do not surface automated-evaluation concepts in the default hackathon UX when the mode is disabled.

## Product requirements from research

Conflux can eventually support more than hackathons—ML challenges, programming contests, benchmarks, data competitions—without putting those concepts into the default hackathon UI.
- OPTIONAL — event template for automatic metric-based competition.
- OPTIONAL — hidden/public test split.
- OPTIONAL — submission attempt limits.
- OPTIONAL — queued evaluation jobs.
- OPTIONAL — leaderboard.
- OPTIONAL — frozen evaluation container/image/version.
- OPTIONAL — custom metric plugin.
- OPTIONAL — anti-leakage/public-private leaderboard policy.
- OPTIONAL — code submission from pinned repository/artifact.
- OPTIONAL — benchmark result artifact and logs.
- OPTIONAL — compute quota.
- OPTIONAL — manual judging + automated metric hybrid.
- EXPERT — sandbox isolation/resource limits.
- EXPERT — reproducibility bundle.
- EXPERT — evaluation rerun under new metric version is clearly distinguished from original official result.
- PROG — evaluator extension interface independent of core judging.

## Batch scope

### PD-S062-B01 — Optional automated-evaluation competition modes — event template for automatic metric-bas… → anti-leakage/public-private leaderboard…

- event template for automatic metric-based competition
- hidden/public test split
- submission attempt limits
- queued evaluation jobs
- leaderboard
- frozen evaluation container/image/version
- custom metric plugin
- anti-leakage/public-private leaderboard policy

### PD-S062-B02 — Optional automated-evaluation competition modes — code submission from pinned repository/… → evaluator extension interface independe…

- code submission from pinned repository/artifact
- benchmark result artifact and logs
- compute quota
- manual judging + automated metric hybrid
- sandbox isolation/resource limits
- reproducibility bundle
- evaluation rerun under new metric version is clearly distinguished from original official result
- evaluator extension interface independent of core judging

