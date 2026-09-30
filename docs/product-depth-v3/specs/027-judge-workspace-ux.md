# PD-S027 — Judge workspace UX

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §27  
**Queue batches:** PD-S027-B01, PD-S027-B02, PD-S027-B03

## Completion interpretation

This specification is the canonical depth contract for §27. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Judge UI must preserve the frozen evidence package and never expose peer ballots unless an explicit authorized deliberation role permits it.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `PREVIEW_CONTEXT`
- `RICH_DOC`
- `ROUTER`
- `SCHEMA_EDITOR`
- `THREADS`
- `TIMELINE`

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
| `archive` | required |
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

The judge surface should optimize for speed, focus, evidence quality and mistake prevention.
- BASE — queue left, project/evidence center, rubric right on wide screens.
- BASE — focused single-column mode on smaller screens.
- BASE — autosave with obvious saved/offline/error state.
- BASE — keyboard next/previous and scoring shortcuts.
- BASE — assignment progress.
- BASE — conflict/recusal always accessible.
- BASE — exact frozen submission evidence.
- ADV — resize/collapse panes.
- ADV — artifact tabs with preserved position.
- ADV — personal notes with explicit visibility.
- ADV — compare against rubric anchors.
- ADV — flag project for organizer review without changing score.
- ADV — offline draft buffer with deterministic reconciliation.
- ADV — route/schedule integration for physical events.
- ADV — time budget/pacing indicator.
- ADV — accessibility preference including high-contrast and text sizing.
- EXPERT — dual-project compare mode for pairwise.
- EXPERT — configurable judge workspace layout by evaluation method.
- EXPERT — local keyboard macro profile for high-volume judging.

## Batch scope

### PD-S027-B01 — Judge workspace UX — queue left, project/evidence center, ru… → resize/collapse panes

- queue left, project/evidence center, rubric right on wide screens
- focused single-column mode on smaller screens
- autosave with obvious saved/offline/error state
- keyboard next/previous and scoring shortcuts
- assignment progress
- conflict/recusal always accessible
- exact frozen submission evidence
- resize/collapse panes

### PD-S027-B02 — Judge workspace UX — artifact tabs with preserved position → accessibility preference including high…

- artifact tabs with preserved position
- personal notes with explicit visibility
- compare against rubric anchors
- flag project for organizer review without changing score
- offline draft buffer with deterministic reconciliation
- route/schedule integration for physical events
- time budget/pacing indicator
- accessibility preference including high-contrast and text sizing

### PD-S027-B03 — Judge workspace UX — dual-project compare mode for pairwise → local keyboard macro profile for high-v…

- dual-project compare mode for pairwise
- configurable judge workspace layout by evaluation method
- local keyboard macro profile for high-volume judging

