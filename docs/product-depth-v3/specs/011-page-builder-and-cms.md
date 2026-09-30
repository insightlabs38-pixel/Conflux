# PD-S011 — Page builder and CMS

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §11  
**Queue batches:** PD-S011-B01, PD-S011-B02, PD-S011-B03, PD-S011-B04

## Completion interpretation

This specification is the canonical depth contract for §11. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `EXTENSION_MANIFEST`
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `VERSION_DIFF`

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

The existing schema-driven block model can become a Shopify-like compositional system without becoming a generic website builder.
- BASE — drag reorder sections.
- BASE — live preview.
- BASE — block presets with excellent defaults.
- BASE — undo/redo.
- BASE — autosave draft vs explicit publish.
- BASE — page-level publication status.
- ADV — nested blocks with bounded depth.
- ADV — reusable block/section instances.
- ADV — copy/paste blocks between pages/events.
- ADV — global reusable content snippets.
- ADV — conditional blocks by lifecycle/date/audience.
- ADV — block-level visibility rules.
- ADV — block version history and visual diff.
- ADV — multi-device preview.
- ADV — draft preview links.
- ADV — block presets grouped by purpose.
- ADV — dynamic data blocks driven by saved queries.
- ADV — per-block analytics impressions/clicks where privacy policy allows.
- ADV — localization variants.
- EXPERT — extension-contributed block types with declared schemas.
- EXPERT — block compatibility/version migrations.
- EXPERT — page templates and page-template inheritance.
- EXPERT — static safety analysis for broken links, missing media, inaccessible headings and excessive layout cost.
- PROG — canonical JSON/YAML page representation.
- PROG — schema-generated basic editor for any extension block.

## Batch scope

### PD-S011-B01 — Page builder and CMS — drag reorder sections → reusable block/section instances

- drag reorder sections
- live preview
- block presets with excellent defaults
- undo/redo
- autosave draft vs explicit publish
- page-level publication status
- nested blocks with bounded depth
- reusable block/section instances

### PD-S011-B02 — Page builder and CMS — copy/paste blocks between pages/events → block presets grouped by purpose

- copy/paste blocks between pages/events
- global reusable content snippets
- conditional blocks by lifecycle/date/audience
- block-level visibility rules
- block version history and visual diff
- multi-device preview
- draft preview links
- block presets grouped by purpose

### PD-S011-B03 — Page builder and CMS — dynamic data blocks driven by saved que… → canonical JSON/YAML page representation

- dynamic data blocks driven by saved queries
- per-block analytics impressions/clicks where privacy policy allows
- localization variants
- extension-contributed block types with declared schemas
- block compatibility/version migrations
- page templates and page-template inheritance
- static safety analysis for broken links, missing media, inaccessible headings and excessive layout cost
- canonical JSON/YAML page representation

### PD-S011-B04 — Page builder and CMS — schema-generated basic editor for any extension block

- schema-generated basic editor for any extension block

