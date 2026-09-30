# PD-S123 — “Open in split view” everywhere it saves navigation

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §123  
**Queue batches:** PD-S123-B01

## Completion interpretation

This specification is the canonical depth contract for §123. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Split view is a reusable interaction pattern, not bespoke duplicated detail panes per module.

## Canonical primitive reuse

- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `DATA_GRID`
- `RICH_DOC`
- `ROUTER`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | not_required |
| `sdk` | not_required |
| `cli` | not_required |
| `mcp` | not_required |
| `event_as_code` | not_required |
| `audit` | not_required |
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

Useful examples:

- participant table → profile/application;
- project table → submission/evidence;
- judge table → workload/conflicts;
- awards table → candidate evidence;
- help desk → participant/project;
- sponsor challenge → eligible projects.

**Outcome:** operator throughput without huge screen redesigns.

## Batch scope

### PD-S123-B01 — “Open in split view” everywhere it saves navigation — Split-view workflow: participant table… → Split-view workflow: sponsor challenge…

- Split-view workflow: participant table → profile/application
- Split-view workflow: project table → submission/evidence
- Split-view workflow: judge table → workload/conflicts
- Split-view workflow: awards table → candidate evidence
- Split-view workflow: help desk → participant/project
- Split-view workflow: sponsor challenge → eligible projects

