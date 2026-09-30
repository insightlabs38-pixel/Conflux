# PD-S009 — Public event site

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §9  
**Queue batches:** PD-S009-B01, PD-S009-B02, PD-S009-B03

## Completion interpretation

This specification is the canonical depth contract for §9. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `DATA_GRID`
- `NOTIFICATIONS`
- `POLICY_EXPLAIN`
- `RICH_DOC`
- `ROUTER`
- `SCHEMA_EDITOR`
- `TIMELINE`
- `VERSION_DIFF`

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
| `archive` | required |
| `analytics` | not_required |
| `search` | required |
| `docs` | required |

## Approved-design references

- `design/public-event`
- `design/public-project`
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

The public site should be a first-class website product, not an authenticated app with public routes.
- BASE — Compact identity header/hero with event name, dates, status and one action.
- BASE — Navigation for overview, schedule, challenges/tracks, projects, results, resources.
- BASE — excellent no-artwork default.
- BASE — SEO metadata, canonical URLs, OpenGraph cards and social images.
- BASE — fast anonymous rendering and cache-friendly data paths.
- BASE — accessible event status and deadline presentation.
- BASE — clear registration / submission / voting state based on current lifecycle.
- ADV — custom domain.
- ADV — event favicon and manifest.
- ADV — per-page metadata and social image.
- ADV — announcement banner with audience/schedule controls.
- ADV — multiple navigation layouts.
- ADV — page visibility windows.
- ADV — per-page access: public, registered, accepted, checked-in, team members.
- ADV — event-specific footer, legal links and sponsor placement.
- ADV — optional countdown block that does not dominate the page.
- ADV — content localization.
- ADV — static archive mode after event closes.
- EXPERT — edge/static pre-render of stable event pages.
- EXPERT — custom redirect map when organizers restructure pages.
- EXPERT — configurable CSP/embed policy by event.
- PROG — page structure exportable as configuration and independently versionable.

## Batch scope

### PD-S009-B01 — Public event site — Compact identity header/hero with event… → custom domain

- Compact identity header/hero with event name, dates, status and one action
- Navigation for overview, schedule, challenges/tracks, projects, results, resources
- excellent no-artwork default
- SEO metadata, canonical URLs, OpenGraph cards and social images
- fast anonymous rendering and cache-friendly data paths
- accessible event status and deadline presentation
- clear registration / submission / voting state based on current lifecycle
- custom domain

### PD-S009-B02 — Public event site — event favicon and manifest → optional countdown block that does not…

- event favicon and manifest
- per-page metadata and social image
- announcement banner with audience/schedule controls
- multiple navigation layouts
- page visibility windows
- per-page access: public, registered, accepted, checked-in, team members
- event-specific footer, legal links and sponsor placement
- optional countdown block that does not dominate the page

### PD-S009-B03 — Public event site — content localization → page structure exportable as configurat…

- content localization
- static archive mode after event closes
- edge/static pre-render of stable event pages
- custom redirect map when organizers restructure pages
- configurable CSP/embed policy by event
- page structure exportable as configuration and independently versionable

