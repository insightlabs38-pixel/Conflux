# PD-S008 — Event templates, presets, cloning and reusable modules

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §8  
**Queue batches:** PD-S008-B01, PD-S008-B02

## Completion interpretation

This specification is the canonical depth contract for §8. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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

Templates should evolve from “copy this event” into a reusable, versioned product primitive.
- BASE — Curated built-in templates with opinionated defaults.
- BASE — Preview a template before creating an event.
- BASE — Template explains which features it enables and why.
- ADV — Workspace template library.
- ADV — Versioned templates; existing events retain their pinned version.
- ADV — Upgrade preview from template v2 to v3.
- ADV — Template parameters: event name, dates, team size, judging duration, tracks.
- ADV — Optional template modules: mentor program, expo, sponsor challenges, community voting.
- ADV — Share/import/export templates.
- EXPERT — Composable modules with declared inputs, outputs and compatibility constraints.
- EXPERT — Organization baseline + event overlay.
- EXPERT — Template policy constraints: e.g. mandatory code-of-conduct acknowledgement.
- EXPERT — Template test suite run against synthetic event scenarios.
- EXPERT — Semantic migration hooks when a module version changes.
- PROG — Template/module registry used identically by UI and Event-as-Code.

## Batch scope

### PD-S008-B01 — Event templates, presets, cloning and reusable modules — Curated built-in templates with opinion… → Optional template modules: mentor progr…

- Curated built-in templates with opinionated defaults
- Preview a template before creating an event
- Template explains which features it enables and why
- Workspace template library
- Versioned templates; existing events retain their pinned version
- Upgrade preview from template v2 to v3
- Template parameters: event name, dates, team size, judging duration, tracks
- Optional template modules: mentor program, expo, sponsor challenges, community voting

### PD-S008-B02 — Event templates, presets, cloning and reusable modules — Share/import/export templates → Template/module registry used identical…

- Share/import/export templates
- Composable modules with declared inputs, outputs and compatibility constraints
- Organization baseline + event overlay
- Template policy constraints: e.g. mandatory code-of-conduct acknowledgement
- Template test suite run against synthetic event scenarios
- Semantic migration hooks when a module version changes
- Template/module registry used identically by UI and Event-as-Code

