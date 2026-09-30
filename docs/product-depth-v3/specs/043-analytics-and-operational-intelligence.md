# PD-S043 — Analytics and operational intelligence

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §43  
**Queue batches:** PD-S043-B01, PD-S043-B02, PD-S043-B03

## Completion interpretation

This specification is the canonical depth contract for §43. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `POLICY_EXPLAIN`
- `QUERY`
- `RICH_DOC`
- `SAVED_VIEWS`
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
| `archive` | not_required |
| `analytics` | required |
| `search` | required |
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

Analytics should answer operational questions, not merely display decorative charts.
- BASE — registration/application/team/project/submission funnel.
- BASE — judging completion and workload.
- BASE — check-in counts.
- BASE — mentor queue state.
- BASE — award/publication readiness.
- ADV — segment by track/cohort/status/custom taxonomy.
- ADV — time-series for submissions/finalizations near deadline.
- ADV — filterable distributions for judge scoring.
- ADV — query-to-chart from saved views.
- ADV — export underlying rows.
- ADV — data freshness timestamp.
- ADV — event health panel with actionable threshold alerts.
- ADV — compare current event against its own prior stage or prior edition.
- ADV — custom dashboard layout.
- EXPERT — anomaly detection only where explainable and actionable.
- EXPERT — capacity forecasting using observed workload.
- EXPERT — privacy-aware aggregate suppression for small groups.
- PROG — analytics metrics have documented definitions and versioning.

## Batch scope

### PD-S043-B01 — Analytics and operational intelligence — registration/application/team/project/s… → filterable distributions for judge scor…

- registration/application/team/project/submission funnel
- judging completion and workload
- check-in counts
- mentor queue state
- award/publication readiness
- segment by track/cohort/status/custom taxonomy
- time-series for submissions/finalizations near deadline
- filterable distributions for judge scoring

### PD-S043-B02 — Analytics and operational intelligence — query-to-chart from saved views → capacity forecasting using observed wor…

- query-to-chart from saved views
- export underlying rows
- data freshness timestamp
- event health panel with actionable threshold alerts
- compare current event against its own prior stage or prior edition
- custom dashboard layout
- anomaly detection only where explainable and actionable
- capacity forecasting using observed workload

### PD-S043-B03 — Analytics and operational intelligence — privacy-aware aggregate suppression for… → analytics metrics have documented defin…

- privacy-aware aggregate suppression for small groups
- analytics metrics have documented definitions and versioning

