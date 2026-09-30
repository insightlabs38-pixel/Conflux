# PD-S116 — Event “doctor” and operator readiness diagnostics

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §116  
**Queue batches:** PD-S116-B01, PD-S116-B02, PD-S116-B03

## Completion interpretation

This specification is the canonical depth contract for §116. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Event Doctor is the canonical diagnostic registry/operator surface. Other readiness flows should register/reuse diagnostics rather than copy logic.

## Canonical primitive reuse

- `APPROVAL`
- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `NOTIFICATIONS`
- `POLICY_EXPLAIN`
- `RICH_DOC`
- `SCHEMA_EDITOR`
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
| `webhook` | required |
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

This should go beyond deployment health.

One command/page could inspect:

- missing event dates;
- contradictory deadlines;
- no published rules;
- no registration path;
- prize without selection method;
- award with no eligible projects;
- judge capacity shortage;
- disconnected assignment graph;
- judge conflicts unresolved;
- unpublished rubric;
- required submission field not exposed;
- broken public links/media;
- page block with inaccessible contrast;
- venue rooms over capacity;
- checked-in attendees without necessary consent;
- scheduled announcement with empty audience;
- webhook failures;
- backup too old;
- stale sponsor resource;
- results publication approval incomplete.

**Why include:** This is the useful version of “verification depth”: it catches actual event failures.

## Batch scope

### PD-S116-B01 — Event “doctor” and operator readiness diagnostics — Event Doctor diagnostic: missing event… → Event Doctor diagnostic: disconnected a…

- Event Doctor diagnostic: missing event dates
- Event Doctor diagnostic: contradictory deadlines
- Event Doctor diagnostic: no published rules
- Event Doctor diagnostic: no registration path
- Event Doctor diagnostic: prize without selection method
- Event Doctor diagnostic: award with no eligible projects
- Event Doctor diagnostic: judge capacity shortage
- Event Doctor diagnostic: disconnected assignment graph

### PD-S116-B02 — Event “doctor” and operator readiness diagnostics — Event Doctor diagnostic: judge conflict… → Event Doctor diagnostic: scheduled anno…

- Event Doctor diagnostic: judge conflicts unresolved
- Event Doctor diagnostic: unpublished rubric
- Event Doctor diagnostic: required submission field not exposed
- Event Doctor diagnostic: broken public links/media
- Event Doctor diagnostic: page block with inaccessible contrast
- Event Doctor diagnostic: venue rooms over capacity
- Event Doctor diagnostic: checked-in attendees without necessary consent
- Event Doctor diagnostic: scheduled announcement with empty audience

### PD-S116-B03 — Event “doctor” and operator readiness diagnostics — Event Doctor diagnostic: webhook failur… → Event Doctor diagnostic: results public…

- Event Doctor diagnostic: webhook failures
- Event Doctor diagnostic: backup too old
- Event Doctor diagnostic: stale sponsor resource
- Event Doctor diagnostic: results publication approval incomplete

