# PD-S010 — Theme, visual customization and design system

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §10  
**Queue batches:** PD-S010-B01, PD-S010-B02, PD-S010-B03

## Completion interpretation

This specification is the canonical depth contract for §10. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `DATA_GRID`
- `EXTENSION_MANIFEST`
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

Customization should be deep enough that two Conflux events need not look like the same template, while keeping every customization inside accessibility and performance guardrails.
- BASE — curated default theme that needs zero organizer tuning.
- BASE — color palette with automatically derived accessible states.
- BASE — typography presets using safe, performant font stacks.
- BASE — compact/comfortable content density.
- BASE — logo, mark, banner and project-card artwork.
- BASE — hero: none/compact/standard; compact default.
- ADV — design token editor for colors, type scale, radius, spacing, borders and surfaces.
- ADV — light/dark/auto event theme modes.
- ADV — independent public-site and operator-workspace branding boundaries.
- ADV — multiple named theme presets in one event.
- ADV — responsive art direction and crop/focal point.
- ADV — layout width and grid presets.
- ADV — section-level background/surface variants.
- ADV — live WCAG contrast checks during editing.
- ADV — theme diff/history/rollback.
- ADV — export/import theme package.
- EXPERT — CSS-variable extension surface with allowlisted tokens, not arbitrary global CSS by default.
- EXPERT — custom font packages with licensing/size validation.
- EXPERT — event theme compatibility/conformance test across all block types.
- EXPERT — design-token inheritance from organization → event → page → block.
- PROG — theme schema is typed and available to extensions/Event-as-Code.
- PROG — extension blocks declare which theme tokens they consume.

## Batch scope

### PD-S010-B01 — Theme, visual customization and design system — curated default theme that needs zero o… → light/dark/auto event theme modes

- curated default theme that needs zero organizer tuning
- color palette with automatically derived accessible states
- typography presets using safe, performant font stacks
- compact/comfortable content density
- logo, mark, banner and project-card artwork
- hero: none/compact/standard; compact default
- design token editor for colors, type scale, radius, spacing, borders and surfaces
- light/dark/auto event theme modes

### PD-S010-B02 — Theme, visual customization and design system — independent public-site and operator-wo… → export/import theme package

- independent public-site and operator-workspace branding boundaries
- multiple named theme presets in one event
- responsive art direction and crop/focal point
- layout width and grid presets
- section-level background/surface variants
- live WCAG contrast checks during editing
- theme diff/history/rollback
- export/import theme package

### PD-S010-B03 — Theme, visual customization and design system — CSS-variable extension surface with all… → extension blocks declare which theme to…

- CSS-variable extension surface with allowlisted tokens, not arbitrary global CSS by default
- custom font packages with licensing/size validation
- event theme compatibility/conformance test across all block types
- design-token inheritance from organization → event → page → block
- theme schema is typed and available to extensions/Event-as-Code
- extension blocks declare which theme tokens they consume

