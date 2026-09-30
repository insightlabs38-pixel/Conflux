# PD-S097 — Participant surveys and event feedback

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §97  
**Queue batches:** PD-S097-B01, PD-S097-B02

## Completion interpretation

This specification is the canonical depth contract for §97. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `NOTIFICATIONS`
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
| `analytics` | required |
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

A small general form use can produce high-value event learning.

- BASE — post-event participant survey.
- BASE — judge/mentor/volunteer/sponsor survey variants.
- BASE — anonymous or identified mode.
- BASE — reminder.
- BASE — simple results/CSV.
- ADV — NPS-style question if organizer wants it.
- ADV — session/workshop feedback.
- ADV — sponsor-tool feedback.
- ADV — segment aggregate results by role/track without exposing small sensitive groups.
- ADV — recurring-event comparison.
- ADV — turn common complaints into next-event tasks/templates.
- EXPERT — survey templates attached to event presets.

**Why include:** Serious recurring programs need feedback, and Devpost/competitors explicitly advertise survey/reporting.

## Batch scope

### PD-S097-B01 — Participant surveys and event feedback — post-event participant survey → sponsor-tool feedback

- post-event participant survey
- judge/mentor/volunteer/sponsor survey variants
- anonymous or identified mode
- reminder
- simple results/CSV
- NPS-style question if organizer wants it
- session/workshop feedback
- sponsor-tool feedback

### PD-S097-B02 — Participant surveys and event feedback — segment aggregate results by role/track… → survey templates attached to event pres…

- segment aggregate results by role/track without exposing small sensitive groups
- recurring-event comparison
- turn common complaints into next-event tasks/templates
- survey templates attached to event presets

