# PD-S090 — Badge, signage and print center

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §90  
**Queue batches:** PD-S090-B01, PD-S090-B02

## Completion interpretation

This specification is the canonical depth contract for §90. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `BULK_PLAN`
- `DATA_GRID`
- `RICH_DOC`
- `SCHEMA_EDITOR`
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
| `archive` | not_required |
| `analytics` | not_required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- `design/onsite-mobile`
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

The onsite subsystem already has enough structured data to generate useful physical artifacts.

- BASE — badge templates by role.
- BASE — participant name + QR + role.
- BASE — print single/reprint.
- BASE — table/project number cards.
- ADV — sponsor/judge/mentor badge styles.
- ADV — session/room signs.
- ADV — judging table labels.
- ADV — dietary/accessibility indicator only where appropriate and privacy-safe.
- ADV — print queue.
- ADV — batch PDF.
- ADV — parking pass templates.
- ADV — emergency/contact cards.
- EXPERT — label-printer adapter.
- PROG — print layouts use canonical event/person/project data.

**Why include:** MLH literally lists badges/lanyards, parking passes, minor forms and table numbers as things organizers prepare.

## Batch scope

### PD-S090-B01 — Badge, signage and print center — badge templates by role → dietary/accessibility indicator only wh…

- badge templates by role
- participant name + QR + role
- print single/reprint
- table/project number cards
- sponsor/judge/mentor badge styles
- session/room signs
- judging table labels
- dietary/accessibility indicator only where appropriate and privacy-safe

### PD-S090-B02 — Badge, signage and print center — print queue → print layouts use canonical event/perso…

- print queue
- batch PDF
- parking pass templates
- emergency/contact cards
- label-printer adapter
- print layouts use canonical event/person/project data

