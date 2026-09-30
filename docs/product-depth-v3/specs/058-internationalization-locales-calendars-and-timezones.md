# PD-S058 — Internationalization, locales, calendars and timezones

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §58  
**Queue batches:** PD-S058-B01, PD-S058-B02

## Completion interpretation

This specification is the canonical depth contract for §58. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
| `event_as_code` | required |
| `audit` | required |
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

Events are deadline-heavy; timezone behavior must be deeper than translated strings.
- BASE — every deadline stores an unambiguous instant + event timezone context.
- BASE — user sees event timezone and optionally local timezone.
- BASE — DST ambiguity/nonexistent-time warnings in organizer editor.
- ADV — localized UI strings.
- ADV — localized public pages.
- ADV — localized rich-content variants.
- ADV — locale-aware number/date formatting.
- ADV — right-to-left layout support.
- ADV — language preference in profile.
- ADV — message template locale fallback.
- ADV — translated form labels/help while response schema stays stable.
- EXPERT — locale completeness report for an event.
- EXPERT — custom terminology/taxonomy labels by locale.
- PROG — APIs return stable codes, not localized strings as identifiers.

## Batch scope

### PD-S058-B01 — Internationalization, locales, calendars and timezones — every deadline stores an unambiguous in… → right-to-left layout support

- every deadline stores an unambiguous instant + event timezone context
- user sees event timezone and optionally local timezone
- DST ambiguity/nonexistent-time warnings in organizer editor
- localized UI strings
- localized public pages
- localized rich-content variants
- locale-aware number/date formatting
- right-to-left layout support

### PD-S058-B02 — Internationalization, locales, calendars and timezones — language preference in profile → APIs return stable codes, not localized…

- language preference in profile
- message template locale fallback
- translated form labels/help while response schema stays stable
- locale completeness report for an event
- custom terminology/taxonomy labels by locale
- APIs return stable codes, not localized strings as identifiers

