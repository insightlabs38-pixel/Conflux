# PD-S076 — Judge staffing and capacity planner

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §76  
**Queue batches:** PD-S076-B01, PD-S076-B02

## Completion interpretation

This specification is the canonical depth contract for §76. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Capacity planning is decision support with assumptions shown. Historical ratios are optional forecast inputs, not authoritative facts.

## Canonical primitive reuse

- `ASYNC_JOB`
- `POLICY_EXPLAIN`
- `RICH_DOC`

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

Conflux can turn its assignment knowledge into pre-event planning.

- BASE — estimate judge count needed from expected projects, reviews/project, minutes/review and judging window.
- BASE — compare required vs confirmed judges.
- BASE — show capacity shortage before judging begins.
- ADV — incorporate track-specific judge requirements.
- ADV — incorporate physical walking/travel time.
- ADV — incorporate judge availability windows.
- ADV — incorporate sponsor/award pools.
- ADV — scenario slider: 100 / 150 / 200 expected projects.
- ADV — no-show reserve recommendation.
- ADV — forecast latest likely completion.
- ADV — “what if 20% more projects submit?” scenario.
- EXPERT — use historical submission/check-in ratio as an optional forecast input.
- EXPERT — Monte Carlo-style dropout sensitivity only if it produces clear staffing recommendations.

**Why include:** This converts existing solver sophistication into a pre-event decision tool organizers can actually use.

## Batch scope

### PD-S076-B01 — Judge staffing and capacity planner — estimate judge count needed from expect… → scenario slider: 100 / 150 / 200 expect…

- estimate judge count needed from expected projects, reviews/project, minutes/review and judging window
- compare required vs confirmed judges
- show capacity shortage before judging begins
- incorporate track-specific judge requirements
- incorporate physical walking/travel time
- incorporate judge availability windows
- incorporate sponsor/award pools
- scenario slider: 100 / 150 / 200 expected projects

### PD-S076-B02 — Judge staffing and capacity planner — no-show reserve recommendation → Monte Carlo-style dropout sensitivity o…

- no-show reserve recommendation
- forecast latest likely completion
- what if 20% more projects submit?” scenario
- use historical submission/check-in ratio as an optional forecast input
- Monte Carlo-style dropout sensitivity only if it produces clear staffing recommendations

