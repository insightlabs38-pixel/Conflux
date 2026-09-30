# PD-S129 — Default presets for sophisticated systems

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §129  
**Queue batches:** PD-S129-B01

## Completion interpretation

This specification is the canonical depth contract for §129. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Presets are compositions over canonical configuration with explicit defaults and versioning; they must not fork hidden behavior.

## Canonical primitive reuse

- `APPROVAL`
- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `TIMELINE`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | required |
| `sdk` | not_required |
| `cli` | not_required |
| `mcp` | not_required |
| `event_as_code` | required |
| `audit` | required |
| `webhook` | not_required |
| `archive` | not_required |
| `analytics` | not_required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- `design/event-builder`
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

Complexity should arrive with good presets:

- judging: weighted rubric, top-picks, pairwise, hybrid;
- assignment: balanced, expertise-aware, physical science-fair;
- admissions: open, approval, waitlist;
- event: online, hybrid, in-person;
- publication: immediate, scheduled, approval-required;
- feedback: private, anonymous release, named release;
- page: simple, sponsor-heavy, technical challenge.

**Outcome:** advanced backend features become usable by ordinary organizers.

## Batch scope

### PD-S129-B01 — Default presets for sophisticated systems — Default preset: judging: weighted rubri… → Default preset: page: simple, sponsor-h…

- Default preset: judging: weighted rubric, top-picks, pairwise, hybrid
- Default preset: assignment: balanced, expertise-aware, physical science-fair
- Default preset: admissions: open, approval, waitlist
- Default preset: event: online, hybrid, in-person
- Default preset: publication: immediate, scheduled, approval-required
- Default preset: feedback: private, anonymous release, named release
- Default preset: page: simple, sponsor-heavy, technical challenge

