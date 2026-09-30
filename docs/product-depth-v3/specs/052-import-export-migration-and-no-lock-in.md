# PD-S052 — Import, export, migration and no-lock-in

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §52  
**Queue batches:** PD-S052-B01, PD-S052-B02, PD-S052-B03

## Completion interpretation

This specification is the canonical depth contract for §52. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Import/export is dry-run capable, versioned, resumable where needed and produces unsupported-data/failure reports; source identities are provenance, not live identity.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `DATA_GRID`
- `PREVIEW_CONTEXT`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `TYPED_CLIENT`
- `VERSION_DIFF`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | not_required |
| `api` | required |
| `sdk` | required |
| `cli` | required |
| `mcp` | not_required |
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | not_required |
| `archive` | required |
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

No-lock-in should be a product promise backed by concrete migration tooling.
- BASE — canonical configuration export.
- BASE — full event archive export.
- BASE — CSV exports for ordinary entities.
- ADV — migration preview before import.
- ADV — field mapping UI.
- ADV — unsupported-data report.
- ADV — deterministic identity rewriting.
- ADV — media/artifact migration manifest.
- ADV — import dry-run.
- ADV — resumable large migration.
- ADV — adapter for common hackathon exports where formats are available.
- ADV — preserve source-system identifiers as provenance metadata.
- ADV — static public archive export.
- EXPERT — signed portable archive.
- EXPERT — round-trip compatibility tests.
- EXPERT — migration adapter SDK.
- EXPERT — archive schema version migration.
- PROG — migration is observable as async job with per-record failures and retry.

## Batch scope

### PD-S052-B01 — Import, export, migration and no-lock-in — canonical configuration export → media/artifact migration manifest

- canonical configuration export
- full event archive export
- CSV exports for ordinary entities
- migration preview before import
- field mapping UI
- unsupported-data report
- deterministic identity rewriting
- media/artifact migration manifest

### PD-S052-B02 — Import, export, migration and no-lock-in — import dry-run → migration adapter SDK

- import dry-run
- resumable large migration
- adapter for common hackathon exports where formats are available
- preserve source-system identifiers as provenance metadata
- static public archive export
- signed portable archive
- round-trip compatibility tests
- migration adapter SDK

### PD-S052-B03 — Import, export, migration and no-lock-in — archive schema version migration → migration is observable as async job wi…

- archive schema version migration
- migration is observable as async job with per-record failures and retry

