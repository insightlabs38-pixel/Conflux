# PD-S105 — Live result incident / correction playbook

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §105  
**Queue batches:** PD-S105-B01, PD-S105-B02

## Completion interpretation

This specification is the canonical depth contract for §105. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Results publication/correction preserves historical official versions and notification/fulfillment consequences; do not rewrite prior published history.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `NOTIFICATIONS`
- `PREVIEW_CONTEXT`
- `QUERY`
- `RICH_DOC`
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
| `analytics` | not_required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- `design/deliberation-awards`
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

Results publication is high-stakes enough for a dedicated recovery workflow.

- BASE — pre-publish preview.
- BASE — atomic publish.
- BASE — rollback visibility if publication fails before becoming official.
- BASE — correction workflow after official publication.
- ADV — affected award/project list.
- ADV — correction reason.
- ADV — participant notification plan.
- ADV — public correction notice.
- ADV — archive retains previous result version.
- ADV — prize-fulfillment hold when result is disputed/corrected.
- EXPERT — rehearse publication against a demo/rehearsal event.

**Why include:** Prevents the worst possible “live projector + wrong winners” scenario and reuses existing publication/audit primitives.

## Batch scope

### PD-S105-B01 — Live result incident / correction playbook — pre-publish preview → public correction notice

- pre-publish preview
- atomic publish
- rollback visibility if publication fails before becoming official
- correction workflow after official publication
- affected award/project list
- correction reason
- participant notification plan
- public correction notice

### PD-S105-B02 — Live result incident / correction playbook — archive retains previous result version → rehearse publication against a demo/reh…

- archive retains previous result version
- prize-fulfillment hold when result is disputed/corrected
- rehearse publication against a demo/rehearsal event

