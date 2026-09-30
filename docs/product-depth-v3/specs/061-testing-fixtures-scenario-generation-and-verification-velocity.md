# PD-S061 — Testing, fixtures, scenario generation and verification velocity

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §61  
**Queue batches:** PD-S061-B01, PD-S061-B02, PD-S061-B03

## Completion interpretation

This specification is the canonical depth contract for §61. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Verification architecture must favor isolated deterministic fixtures and tiered suites. Slow release tests are not allowed to make the normal developer loop unusable.

## Canonical primitive reuse

- `APPROVAL`
- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `DATA_GRID`
- `EXTENSION_MANIFEST`
- `POLICY_EXPLAIN`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `TIMELINE`
- `TYPED_CLIENT`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | not_required |
| `api` | not_required |
| `sdk` | required |
| `cli` | required |
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

Given the hackathon experience, the verification architecture itself is a product-development multiplier.
- BASE — backend fast tests stay fast; profile slowest tail rather than over-optimize everything.
- BASE — persistent dev stack with HMR.
- BASE — deterministic fixtures.
- BASE — isolated E2E event/workspace per test or shard where mutation occurs.
- BASE — reusable auth storage state.
- BASE — browser traces/screenshots/video on failure by default.
- ADV — affected-test selection.
- ADV — smoke / PR / full / release browser tiers.
- ADV — scenario generator for event sizes and enabled feature combinations.
- ADV — fixtures for each lifecycle state.
- ADV — time-control helpers for deadline testing.
- ADV — concurrency harness for finalize/vote/score/publish races.
- ADV — visual regression for stable critical surfaces.
- ADV — accessibility regression.
- ADV — API/SDK schema drift gate.
- EXPERT — mutation/property testing for policy and workflow invariants.
- EXPERT — chaos suite.
- EXPERT — performance regression budget by endpoint/workload.
- EXPERT — extension conformance suite.
- PROG — every reference scenario can be generated via CLI for contributors and demos.

## Batch scope

### PD-S061-B01 — Testing, fixtures, scenario generation and verification velocity — backend fast tests stay fast; profile s… → smoke / PR / full / release browser tie…

- backend fast tests stay fast; profile slowest tail rather than over-optimize everything
- persistent dev stack with HMR
- deterministic fixtures
- isolated E2E event/workspace per test or shard where mutation occurs
- reusable auth storage state
- browser traces/screenshots/video on failure by default
- affected-test selection
- smoke / PR / full / release browser tiers

### PD-S061-B02 — Testing, fixtures, scenario generation and verification velocity — scenario generator for event sizes and… → mutation/property testing for policy an…

- scenario generator for event sizes and enabled feature combinations
- fixtures for each lifecycle state
- time-control helpers for deadline testing
- concurrency harness for finalize/vote/score/publish races
- visual regression for stable critical surfaces
- accessibility regression
- API/SDK schema drift gate
- mutation/property testing for policy and workflow invariants

### PD-S061-B03 — Testing, fixtures, scenario generation and verification velocity — chaos suite → every reference scenario can be generat…

- chaos suite
- performance regression budget by endpoint/workload
- extension conformance suite
- every reference scenario can be generated via CLI for contributors and demos

