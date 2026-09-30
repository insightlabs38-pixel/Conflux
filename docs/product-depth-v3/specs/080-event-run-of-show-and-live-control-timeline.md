# PD-S080 — Event run-of-show and live control timeline

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §80  
**Queue batches:** PD-S080-B01, PD-S080-B02

## Completion interpretation

This specification is the canonical depth contract for §80. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Run-of-show is an operational timeline linked to canonical event milestones; it does not duplicate public schedule state.

## Canonical primitive reuse

- `ASYNC_JOB`
- `BULK_PLAN`
- `NOTIFICATIONS`
- `PREVIEW_CONTEXT`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `THREADS`
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

A schedule tells attendees what happens. A **run-of-show** tells organizers what needs to happen behind the scenes.

- BASE — operational timeline separate from public schedule.
- BASE — tasks with owner, due time and status.
- BASE — dependencies.
- BASE — role/team assignment.
- BASE — “happening now / next 30 minutes / overdue.”
- ADV — reusable templates: doors open, meal arrival, submission freeze, judge briefing, judging start, finalists, closing.
- ADV — private notes and contingency instructions.
- ADV — attach runbook/checklist.
- ADV — confirm critical milestones.
- ADV — bulk “mark ready.”
- ADV — last-minute delay shifts downstream target times with preview.
- ADV — communication action linked to milestone.
- ADV — incident linked to timeline.
- EXPERT — rehearsal mode / dry run.
- PROG — timeline hooks can fire deterministic reminders, never autonomous irreversible operations.

**Why include:** This is core event management work and prevents Conflux from stopping at the competition boundary.

## Batch scope

### PD-S080-B01 — Event run-of-show and live control timeline — operational timeline separate from publ… → attach runbook/checklist

- operational timeline separate from public schedule
- tasks with owner, due time and status
- dependencies
- role/team assignment
- happening now / next 30 minutes / overdue
- reusable templates: doors open, meal arrival, submission freeze, judge briefing, judging start, finalists, closing
- private notes and contingency instructions
- attach runbook/checklist

### PD-S080-B02 — Event run-of-show and live control timeline — confirm critical milestones → timeline hooks can fire deterministic r…

- confirm critical milestones
- bulk “mark ready
- last-minute delay shifts downstream target times with preview
- communication action linked to milestone
- incident linked to timeline
- rehearsal mode / dry run
- timeline hooks can fire deterministic reminders, never autonomous irreversible operations

