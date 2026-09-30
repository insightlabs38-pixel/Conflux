# PD-S078 — Judge no-show and live reassignment mode

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §78  
**Queue batches:** PD-S078-B01, PD-S078-B02

## Completion interpretation

This specification is the canonical depth contract for §78. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Live repair preserves completed ballots and hard conflict/capacity constraints; it only reassigns unfinished obligations unless an explicit correction workflow says otherwise.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `POLICY_EXPLAIN`
- `RICH_DOC`
- `ROUTER`

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

Normal assignment planning is not enough for real events.

- BASE — mark judge unavailable/no-show.
- BASE — immediately show impacted projects.
- BASE — suggest safe replacement assignments.
- BASE — preserve completed ballots.
- ADV — reserve judge pool.
- ADV — reassign only unfinished obligations.
- ADV — physical-route recalculation.
- ADV — notify affected judge/organizer.
- ADV — restore judge if they return.
- ADV — explain any resulting coverage/connectivity degradation.
- EXPERT — rapid repair plan that minimizes movement and workload disruption while preserving hard constraints.

**Why include:** High-value use of existing assignment algorithms during the exact period organizers are under maximum pressure.

## Batch scope

### PD-S078-B01 — Judge no-show and live reassignment mode — mark judge unavailable/no-show → notify affected judge/organizer

- mark judge unavailable/no-show
- immediately show impacted projects
- suggest safe replacement assignments
- preserve completed ballots
- reserve judge pool
- reassign only unfinished obligations
- physical-route recalculation
- notify affected judge/organizer

### PD-S078-B02 — Judge no-show and live reassignment mode — restore judge if they return → rapid repair plan that minimizes moveme…

- restore judge if they return
- explain any resulting coverage/connectivity degradation
- rapid repair plan that minimizes movement and workload disruption while preserving hard constraints

