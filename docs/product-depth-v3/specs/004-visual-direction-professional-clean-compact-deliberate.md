# PD-F004 — Visual direction: professional, clean, compact, deliberate

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §4  
**Queue batches:** PD-F004-B01, PD-F004-B02, PD-F004-B03, PD-F004-B04, PD-F004-B05

## Completion interpretation

This specification is the canonical depth contract for §4. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Claude Design v3 output is the visual source of truth. Current repository styling is legacy context, not an aesthetic constraint.
- Anti-slop rules are persistent design/gate criteria; they are not one-time feature tasks.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `DATA_GRID`
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`

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

Conflux should explicitly reject several common low-quality SaaS/AI-generated UI patterns.

### Default visual language

- BASE: neutral, content-first application shell.
- BASE: modest border radii; avoid turning every region into a giant rounded card.
- BASE: controlled use of elevation; borders and spacing should establish most hierarchy.
- BASE: strong typography scale with fewer arbitrary font sizes.
- BASE: consistent spacing tokens and optical alignment.
- BASE: one primary action per local context; secondary actions remain visibly subordinate.
- BASE: iconography used where it improves recognition, not as decoration.
- BASE: muted color for structure; saturated color reserved for status and action.
- BASE: semantic status colors have icon/text redundancy and accessible contrast.
- BASE: motion communicates state transition; no ambient motion added merely for “polish.”
- BASE: skeletons only where layout is predictable; otherwise clear progress indicators.
- BASE: empty states tell the user the next useful action.
- BASE: error states explain whether data was preserved and what can be retried.
- BASE: “advanced” never means visually chaotic.

### Hero policy

- BASE: **compact hero is the default**, not a viewport-consuming marketing hero.
- BASE: organizer can choose `none`, `compact`, or `standard`.
- ADV: “immersive” / artwork-heavy hero is opt-in for events that deliberately want it.
- BASE: compact hero should usually fit event identity, date/status and one primary action in roughly 160–280 px on desktop.
- BASE: on project pages, project content should begin above or near the fold; avoid a decorative hero that pushes evidence down.
- BASE: on mobile, hero height should collapse aggressively.
- ADV: hero can be replaced with an event-specific lead block.
- ADV: image focal point/crop and responsive art direction.
- ADV: organizer preview at desktop/tablet/mobile.
- BASE: fallback identity should still look intentional when no artwork exists.

### Anti-slop rules

- Do not use gradients by default.
- Do not put icons in colored squares next to every heading.
- Do not use giant KPI cards when a compact summary strip or table is better.
- Do not use oversized marketing copy inside authenticated operator workflows.
- Do not overuse pills/badges for ordinary text.
- Do not make every section a card inside another card.
- Do not repeat the same label in heading, breadcrumb and card title.
- Do not hide frequently used actions behind three-dot menus merely to appear clean.
- Do not use a 3-column dashboard where the organizer needs a sortable data table.
- Do not make destructive operations red until the action itself; avoid a page covered in alarm colors.
- Do not add fake “AI” affordances to ordinary deterministic workflows.
- Do not display unhelpful decimals/precision just because the backend has them.
- Do not make advanced capabilities depend on memorizing opaque IDs.

## Batch scope

### PD-F004-B01 — Visual direction: professional, clean, compact, deliberate — neutral, content-first application shell → muted color for structure; saturated co…

- neutral, content-first application shell
- modest border radii; avoid turning every region into a giant rounded card
- controlled use of elevation; borders and spacing should establish most hierarchy
- strong typography scale with fewer arbitrary font sizes
- consistent spacing tokens and optical alignment
- one primary action per local context; secondary actions remain visibly subordinate
- iconography used where it improves recognition, not as decoration
- muted color for structure; saturated color reserved for status and action

### PD-F004-B02 — Visual direction: professional, clean, compact, deliberate — semantic status colors have icon/text r… → organizer can choose none, compact, or…

- semantic status colors have icon/text redundancy and accessible contrast
- motion communicates state transition; no ambient motion added merely for “polish
- skeletons only where layout is predictable; otherwise clear progress indicators
- empty states tell the user the next useful action
- error states explain whether data was preserved and what can be retried
- advanced” never means visually chaotic
- compact hero is the default, not a viewport-consuming marketing hero
- organizer can choose `none`, `compact`, or `standard`

### PD-F004-B03 — Visual direction: professional, clean, compact, deliberate — immersive” / artwork-heavy hero is opt-… → fallback identity should still look int…

- immersive” / artwork-heavy hero is opt-in for events that deliberately want it
- compact hero should usually fit event identity, date/status and one primary action in roughly 160–280 px on desktop
- on project pages, project content should begin above or near the fold; avoid a decorative hero that pushes evidence down
- on mobile, hero height should collapse aggressively
- hero can be replaced with an event-specific lead block
- image focal point/crop and responsive art direction
- organizer preview at desktop/tablet/mobile
- fallback identity should still look intentional when no artwork exists

### PD-F004-B04 — Visual direction: professional, clean, compact, deliberate — avoid use gradients by default → avoid hide frequently used actions behi…

- Visual guardrail: avoid use gradients by default
- Visual guardrail: avoid put icons in colored squares next to every heading
- Visual guardrail: avoid use giant KPI cards when a compact summary strip or table is better
- Visual guardrail: avoid use oversized marketing copy inside authenticated operator workflows
- Visual guardrail: avoid overuse pills/badges for ordinary text
- Visual guardrail: avoid make every section a card inside another card
- Visual guardrail: avoid repeat the same label in heading, breadcrumb and card title
- Visual guardrail: avoid hide frequently used actions behind three-dot menus merely to appear clean

### PD-F004-B05 — Visual direction: professional, clean, compact, deliberate — avoid use a 3-column dashboard where th… → avoid make advanced capabilities depend…

- Visual guardrail: avoid use a 3-column dashboard where the organizer needs a sortable data table
- Visual guardrail: avoid make destructive operations red until the action itself; avoid a page covered in alarm colors
- Visual guardrail: avoid add fake “AI” affordances to ordinary deterministic workflows
- Visual guardrail: avoid display unhelpful decimals/precision just because the backend has them
- Visual guardrail: avoid make advanced capabilities depend on memorizing opaque IDs

