# PD-S117 — What-if simulator for event operations

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §117  
**Queue batches:** PD-S117-B01, PD-S117-B02

## Completion interpretation

This specification is the canonical depth contract for §117. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Build one non-mutating parameterized simulation framework. Listed 'what if' cases are fixtures/acceptance scenarios, not bespoke calculators.
- Every result shows assumptions, affected entities, infeasible constraints and diff from live state.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `NOTIFICATIONS`
- `POLICY_EXPLAIN`
- `RICH_DOC`
- `TIMELINE`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | required |
| `sdk` | not_required |
| `cli` | required |
| `mcp` | required |
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | not_required |
| `archive` | not_required |
| `analytics` | required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

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

A generalized “what if?” surface can reuse existing planning primitives.

Useful questions:

- What if submissions are 30% higher than expected?
- What if 4 judges cancel?
- What if registration capacity changes from 500 to 600?
- What if judging shrinks from 180 to 120 minutes?
- What if we move the deadline by 30 minutes?
- What if a sponsor challenge requires a new artifact?
- What if one room becomes unavailable?
- What if a track has twice the expected projects?
- What if we prohibit projects from winning more than one sponsor award?

The output should show:

- affected people/projects;
- infeasible constraints;
- extra staffing/capacity;
- changed communication audience;
- expected judging workload;
- resulting award/eligibility changes where deterministic.

**Why include:** Conflux already has the underlying models; this makes them decision support rather than configuration machinery.

## Batch scope

### PD-S117-B01 — Operational simulator — demand, judge, capacity, time, deadline, sponsor, venue and track-load scenarios

- What-if scenario: What if submissions are 30% higher than expected?
- What-if scenario: What if 4 judges cancel?
- What-if scenario: What if registration capacity changes from 500 to 600?
- What-if scenario: What if judging shrinks from 180 to 120 minutes?
- What-if scenario: What if we move the deadline by 30 minutes?
- What-if scenario: What if a sponsor challenge requires a new artifact?
- What-if scenario: What if one room becomes unavailable?
- What-if scenario: What if a track has twice the expected projects?

### PD-S117-B02 — Operational simulator — award-policy scenarios and result contract

- What-if scenario: What if we prohibit projects from winning more than one sponsor award?
- What-if simulator output: affected people/projects
- What-if simulator output: infeasible constraints
- What-if simulator output: extra staffing/capacity
- What-if simulator output: changed communication audience
- What-if simulator output: expected judging workload
- What-if simulator output: resulting award/eligibility changes where deterministic

