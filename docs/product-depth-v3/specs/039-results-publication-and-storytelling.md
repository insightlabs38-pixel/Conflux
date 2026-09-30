# PD-S039 — Results, publication and storytelling

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §39  
**Queue batches:** PD-S039-B01, PD-S039-B02, PD-S039-B03

## Completion interpretation

This specification is the canonical depth contract for §39. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`
- `QUERY`
- `RICH_DOC`
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
| `webhook` | required |
| `archive` | required |
| `analytics` | required |
| `search` | not_required |
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

Publication should turn complex judging evidence into a clean, credible public outcome.
- BASE — winners by award/track.
- BASE — project cards and links.
- BASE — publication preview.
- BASE — scheduled publication.
- ADV — finalist pages.
- ADV — organizer-written result narrative.
- ADV — shareable winner cards.
- ADV — result correction notices with visible history.
- ADV — feedback release independently scheduled from winners.
- ADV — per-award explanation policy.
- ADV — public judge list where event chooses to publish it.
- ADV — photo/media gallery.
- ADV — statistics/participation recap.
- ADV — sponsor acknowledgment.
- ADV — permanent static archive.
- EXPERT — signed results manifest.
- EXPERT — machine-readable result feed.
- PROG — publication is atomic across web/API/archive rather than a series of toggles.

## Batch scope

### PD-S039-B01 — Results, publication and storytelling — winners by award/track → result correction notices with visible…

- winners by award/track
- project cards and links
- publication preview
- scheduled publication
- finalist pages
- organizer-written result narrative
- shareable winner cards
- result correction notices with visible history

### PD-S039-B02 — Results, publication and storytelling — feedback release independently schedule… → signed results manifest

- feedback release independently scheduled from winners
- per-award explanation policy
- public judge list where event chooses to publish it
- photo/media gallery
- statistics/participation recap
- sponsor acknowledgment
- permanent static archive
- signed results manifest

### PD-S039-B03 — Results, publication and storytelling — machine-readable result feed → publication is atomic across web/API/ar…

- machine-readable result feed
- publication is atomic across web/API/archive rather than a series of toggles

