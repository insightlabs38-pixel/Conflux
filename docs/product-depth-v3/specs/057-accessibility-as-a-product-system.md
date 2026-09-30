# PD-S057 — Accessibility as a product system

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §57  
**Queue batches:** PD-S057-B01, PD-S057-B02, PD-S057-B03

## Completion interpretation

This specification is the canonical depth contract for §57. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Accessibility is a continuous contract across default and customized themes, dense tables, rich content and extension blocks.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `DATA_GRID`
- `EXTENSION_MANIFEST`
- `RICH_DOC`
- `ROUTER`
- `SCHEMA_EDITOR`

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

- `design/state-matrix`
- `design/system-v3`

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

Conflux already has accessibility work; the target can be continuous conformance rather than one audit.
- BASE — keyboard navigation.
- BASE — visible focus.
- BASE — semantic headings/landmarks.
- BASE — contrast-compliant default theme.
- BASE — form errors tied to fields.
- BASE — status never color-only.
- ADV — theme editor blocks inaccessible combinations.
- ADV — project story lints missing alt text/heading skips.
- ADV — table/grid screen-reader strategy.
- ADV — reduced-motion support.
- ADV — text scaling without loss of function.
- ADV — math accessibility output.
- ADV — PDF/badge accessibility guidance where technically possible.
- ADV — organizer accessibility conformance report.
- ADV — automated axe-like checks plus documented manual checks.
- EXPERT — extension block conformance contract.
- EXPERT — accessibility snapshot regression suite across themes.
- PROG — accessibility findings have stable machine-readable codes.

## Batch scope

### PD-S057-B01 — Accessibility as a product system — keyboard navigation → project story lints missing alt text/he…

- keyboard navigation
- visible focus
- semantic headings/landmarks
- contrast-compliant default theme
- form errors tied to fields
- status never color-only
- theme editor blocks inaccessible combinations
- project story lints missing alt text/heading skips

### PD-S057-B02 — Accessibility as a product system — table/grid screen-reader strategy → extension block conformance contract

- table/grid screen-reader strategy
- reduced-motion support
- text scaling without loss of function
- math accessibility output
- PDF/badge accessibility guidance where technically possible
- organizer accessibility conformance report
- automated axe-like checks plus documented manual checks
- extension block conformance contract

### PD-S057-B03 — Accessibility as a product system — accessibility snapshot regression suite… → accessibility findings have stable mach…

- accessibility snapshot regression suite across themes
- accessibility findings have stable machine-readable codes

