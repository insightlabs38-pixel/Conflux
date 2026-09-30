# PD-S065 — Custom taxonomies, metadata and semantic organization

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §65  
**Queue batches:** PD-S065-B01, PD-S065-B02

## Completion interpretation

This specification is the canonical depth contract for §65. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `BULK_PLAN`
- `DATA_GRID`
- `PREVIEW_CONTEXT`
- `QUERY`
- `RICH_DOC`
- `SAVED_VIEWS`
- `SCHEMA_EDITOR`

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
| `search` | required |
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

Custom taxonomies can become connective tissue across matching, search, analytics, permissions and content.
- BASE — organizer-defined project/person/event tags.
- ADV — hierarchical taxonomy.
- ADV — synonyms/aliases.
- ADV — controlled vocabulary vs free-form tag distinction.
- ADV — tag colors/icons only where helpful.
- ADV — per-object-type applicability.
- ADV — required/optional taxonomy fields.
- ADV — public/private/internal visibility.
- ADV — taxonomy migration/rename/merge.
- ADV — bulk retagging with preview.
- ADV — taxonomy-driven saved views and page collections.
- EXPERT — taxonomy values as assignment expertise/bid dimensions.
- EXPERT — taxonomy provenance when imported from external system.
- PROG — stable taxonomy IDs independent of display labels/localization.

## Batch scope

### PD-S065-B01 — Custom taxonomies, metadata and semantic organization — organizer-defined project/person/event… → public/private/internal visibility

- organizer-defined project/person/event tags
- hierarchical taxonomy
- synonyms/aliases
- controlled vocabulary vs free-form tag distinction
- tag colors/icons only where helpful
- per-object-type applicability
- required/optional taxonomy fields
- public/private/internal visibility

### PD-S065-B02 — Custom taxonomies, metadata and semantic organization — taxonomy migration/rename/merge → stable taxonomy IDs independent of disp…

- taxonomy migration/rename/merge
- bulk retagging with preview
- taxonomy-driven saved views and page collections
- taxonomy values as assignment expertise/bid dimensions
- taxonomy provenance when imported from external system
- stable taxonomy IDs independent of display labels/localization

