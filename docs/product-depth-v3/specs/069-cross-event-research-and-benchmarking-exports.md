# PD-S069 — Cross-event research and benchmarking exports

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §69  
**Queue batches:** PD-S069-B01, PD-S069-B02

## Completion interpretation

This specification is the canonical depth contract for §69. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

## Canonical primitive reuse

- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `DATA_GRID`
- `POLICY_EXPLAIN`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `VERSION_DIFF`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | not_required |
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

## Product requirements from research

For organizers running recurring programs, careful research exports can be valuable without turning Conflux into an opaque analytics vendor.
- ADV — de-identified export profile.
- ADV — configurable field suppression.
- ADV — stable event/track/stage dimensions.
- ADV — judging diagnostics export.
- ADV — participation funnel export.
- ADV — schema/data dictionary bundled with export.
- ADV — provenance/version of derived metrics.
- EXPERT — longitudinal cross-event project/participant analysis only with appropriate consent/legal basis.
- EXPERT — differential/privacy-preserving techniques are possible future work, not a default claim.
- PROG — export is reproducible from saved query + metric version.

## Batch scope

### PD-S069-B01 — Cross-event research and benchmarking exports — de-identified export profile → longitudinal cross-event project/partic…

- de-identified export profile
- configurable field suppression
- stable event/track/stage dimensions
- judging diagnostics export
- participation funnel export
- schema/data dictionary bundled with export
- provenance/version of derived metrics
- longitudinal cross-event project/participant analysis only with appropriate consent/legal basis

### PD-S069-B02 — Cross-event research and benchmarking exports — differential/privacy-preserving techniq… → export is reproducible from saved query…

- differential/privacy-preserving techniques are possible future work, not a default claim
- export is reproducible from saved query + metric version

