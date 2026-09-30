# PD-F001 — Base experience must remain smaller than the platform

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §1  
**Queue batches:** PD-F001-B01, PD-F001-B02

## Completion interpretation

This specification is the canonical depth contract for §1. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `POLICY_EXPLAIN`
- `QUERY`
- `RICH_DOC`
- `ROUTER`
- `SCHEMA_EDITOR`

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

- No dedicated visual reference is required by default. Any UI introduced still follows the global Conflux v3 design system.

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

A platform can contain 500 capabilities while a new organizer sees only 15 decisions.

- BASE: event creation starts from a high-quality preset with event name, dates, registration, team rules, project requirements, judging method, awards, and publish controls.
- BASE: advanced configuration stays collapsed until a feature requiring it is enabled.
- BASE: sane defaults are real defaults, not placeholder values requiring organizer cleanup.
- BASE: disabled systems disappear from navigation rather than presenting empty tabs.
- BASE: one canonical “event readiness” surface explains what is missing before launch.
- ADV: organizers can progressively switch from presets to custom workflows.
- EXPERT: every default can eventually be overridden where domain invariants permit.
- PROG: defaults and derived values are queryable so automation never has to reverse-engineer UI behavior.
- PROG: generated configuration includes explicit values only when necessary; inherited defaults remain legible.
- BASE: destructive or high-impact operations show consequences, not generic “Are you sure?” dialogs.

## Batch scope

### PD-F001-B01 — Base experience must remain smaller than the platform — event creation starts from a high-quali… → defaults and derived values are queryab…

- event creation starts from a high-quality preset with event name, dates, registration, team rules, project requirements, judging…
- advanced configuration stays collapsed until a feature requiring it is enabled
- sane defaults are real defaults, not placeholder values requiring organizer cleanup
- disabled systems disappear from navigation rather than presenting empty tabs
- one canonical “event readiness” surface explains what is missing before launch
- organizers can progressively switch from presets to custom workflows
- every default can eventually be overridden where domain invariants permit
- defaults and derived values are queryable so automation never has to reverse-engineer UI behavior

### PD-F001-B02 — Base experience must remain smaller than the platform — generated configuration includes explic… → destructive or high-impact operations s…

- generated configuration includes explicit values only when necessary; inherited defaults remain legible
- destructive or high-impact operations show consequences, not generic “Are you sure?” dialogs

