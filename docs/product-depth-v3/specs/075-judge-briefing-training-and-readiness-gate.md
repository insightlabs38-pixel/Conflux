# PD-S075 — Judge briefing, training and readiness gate

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §75  
**Queue batches:** PD-S075-B01, PD-S075-B02

## Completion interpretation

This specification is the canonical depth contract for §75. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Judge briefing/calibration gates release of assignments only when explicitly configured; training completion is separate from official scoring.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
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
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | not_required |
| `archive` | not_required |
| `analytics` | not_required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- `design/judge-review`
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

Conflux's judging math is sophisticated enough that judge readiness deserves first-class support.

- BASE — organizer briefing page containing rubric, timing, event philosophy and logistics.
- BASE — judge acknowledgement before first ballot.
- BASE — example scorecard.
- BASE — clear conflict/recusal instructions.
- BASE — judging-location or remote-call instructions.
- ADV — short calibration/example project.
- ADV — “score this example, then compare with anchors.”
- ADV — required briefing completion if organizer enables it.
- ADV — rubric-change acknowledgement when a published judging configuration changes before judging.
- ADV — judge FAQ.
- ADV — one-click report-a-problem/help request from judging workspace.
- ADV — briefing completion/readiness dashboard.
- EXPERT — organizer can require calibration tolerance before assignments are released.
- EXPERT — different briefing modules per judge pool/award.

**Why include:** MLH explicitly recommends a judging debrief because day-of judge process quality is a major failure mode.

## Batch scope

### PD-S075-B01 — Judge briefing, training and readiness gate — organizer briefing page containing rubr… → required briefing completion if organiz…

- organizer briefing page containing rubric, timing, event philosophy and logistics
- judge acknowledgement before first ballot
- example scorecard
- clear conflict/recusal instructions
- judging-location or remote-call instructions
- short calibration/example project
- score this example, then compare with anchors
- required briefing completion if organizer enables it

### PD-S075-B02 — Judge briefing, training and readiness gate — rubric-change acknowledgement when a pu… → different briefing modules per judge po…

- rubric-change acknowledgement when a published judging configuration changes before judging
- judge FAQ
- one-click report-a-problem/help request from judging workspace
- briefing completion/readiness dashboard
- organizer can require calibration tolerance before assignments are released
- different briefing modules per judge pool/award

