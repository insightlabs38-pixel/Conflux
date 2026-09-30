# PD-S126 — Batch setup from CSV with mapping preview

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §126  
**Queue batches:** PD-S126-B01, PD-S126-B02

## Completion interpretation

This specification is the canonical depth contract for §126. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `BULK_PLAN`
- `PREVIEW_CONTEXT`
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
| `audit` | not_required |
| `webhook` | not_required |
| `archive` | not_required |
| `analytics` | not_required |
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

Useful for:

- participants;
- judges;
- mentors;
- sponsors;
- tracks;
- rooms;
- inventory;
- staff.

Must have:

- mapping preview;
- validation;
- duplicate strategy;
- dry-run;
- error CSV;
- idempotent re-import strategy.

**Outcome:** migration from spreadsheets becomes frictionless.

## Batch scope

### PD-S126-B01 — Batch setup from CSV with mapping preview — CSV setup/import: participants → CSV setup/import: staff

- CSV setup/import: participants
- CSV setup/import: judges
- CSV setup/import: mentors
- CSV setup/import: sponsors
- CSV setup/import: tracks
- CSV setup/import: rooms
- CSV setup/import: inventory
- CSV setup/import: staff

### PD-S126-B02 — Batch setup from CSV with mapping preview — CSV import contract: mapping preview → CSV import contract: idempotent re-impo…

- CSV import contract: mapping preview
- CSV import contract: validation
- CSV import contract: duplicate strategy
- CSV import contract: dry-run
- CSV import contract: error CSV
- CSV import contract: idempotent re-import strategy

