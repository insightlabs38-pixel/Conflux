# PD-S016 — Forms and custom data schemas

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §16  
**Queue batches:** PD-S016-B01, PD-S016-B02, PD-S016-B03

## Completion interpretation

This specification is the canonical depth contract for §16. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `ASYNC_JOB`
- `DATA_GRID`
- `EXTENSION_MANIFEST`
- `NOTIFICATIONS`
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

Forms already exist and are versioned. They can become a general schema system used across applications, submissions, judging and custom event workflows.
- BASE — text, textarea, number, date, select, multiselect, checkbox, URL, email and file fields.
- BASE — required/optional and clear validation messages.
- BASE — field descriptions and examples.
- ADV — conditional visibility based on prior answers.
- ADV — repeating groups.
- ADV — matrix/rating fields.
- ADV — structured person/team/project reference fields.
- ADV — Markdown/help text.
- ADV — field-level audience visibility.
- ADV — computed/read-only fields.
- ADV — reusable field libraries.
- ADV — section/page layout.
- ADV — draft schema vs published immutable schema versions.
- ADV — migration preview when changing schema after responses exist.
- ADV — export schema as JSON Schema-like representation.
- ADV — validation rules beyond simple type constraints.
- EXPERT — cross-field invariant expressions.
- EXPERT — custom extension field types.
- EXPERT — schema compatibility checker.
- EXPERT — schema test examples and fixtures.
- PROG — generated UI, API validation and Event-as-Code all consume the same schema.

## Batch scope

### PD-S016-B01 — Forms and custom data schemas — text, textarea, number, date, select, m… → Markdown/help text

- text, textarea, number, date, select, multiselect, checkbox, URL, email and file fields
- required/optional and clear validation messages
- field descriptions and examples
- conditional visibility based on prior answers
- repeating groups
- matrix/rating fields
- structured person/team/project reference fields
- Markdown/help text

### PD-S016-B02 — Forms and custom data schemas — field-level audience visibility → validation rules beyond simple type con…

- field-level audience visibility
- computed/read-only fields
- reusable field libraries
- section/page layout
- draft schema vs published immutable schema versions
- migration preview when changing schema after responses exist
- export schema as JSON Schema-like representation
- validation rules beyond simple type constraints

### PD-S016-B03 — Forms and custom data schemas — cross-field invariant expressions → generated UI, API validation and Event-…

- cross-field invariant expressions
- custom extension field types
- schema compatibility checker
- schema test examples and fixtures
- generated UI, API validation and Event-as-Code all consume the same schema

