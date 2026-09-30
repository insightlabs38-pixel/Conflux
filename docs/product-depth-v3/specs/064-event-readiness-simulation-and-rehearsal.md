# PD-S064 — Event readiness, simulation and rehearsal

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §64  
**Queue batches:** PD-S064-B01, PD-S064-B02

## Completion interpretation

This specification is the canonical depth contract for §64. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Readiness/rehearsal consumes the canonical diagnostic registry rather than reimplementing checks. Rehearsal state never mutates production event truth.

## Canonical primitive reuse

- `APPROVAL`
- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `NOTIFICATIONS`
- `POLICY_EXPLAIN`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `TIMELINE`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | required |
| `sdk` | not_required |
| `cli` | required |
| `mcp` | required |
| `event_as_code` | required |
| `audit` | required |
| `webhook` | required |
| `archive` | required |
| `analytics` | required |
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

A highly advanced platform should help organizers prove that their configuration works before participants encounter it.
- BASE — pre-launch readiness checklist from actual configuration.
- BASE — test participant/judge accounts.
- ADV — synthetic participant/team/project generator.
- ADV — simulate application → team → submission → eligibility → judging → awards → publish.
- ADV — run deadline transitions in accelerated virtual time.
- ADV — show missing email/template/resource dependencies.
- ADV — detect impossible stage/policy combinations.
- ADV — detect judge capacity shortage before assignments.
- ADV — detect award eligibility impossible/undersubscribed.
- ADV — detect check-in/floorplan capacity issues.
- ADV — verify public-site links/media.
- ADV — dry-run communication audience.
- ADV — dry-run Event-as-Code plan against rehearsal copy.
- EXPERT — stochastic dropout/no-show simulation.
- EXPERT — deadline surge load scenario generated from current event size.
- EXPERT — “launch certification” evidence report.

## Batch scope

### PD-S064-B01 — Event readiness, simulation and rehearsal — pre-launch readiness checklist from act… → detect judge capacity shortage before a…

- pre-launch readiness checklist from actual configuration
- test participant/judge accounts
- synthetic participant/team/project generator
- simulate application → team → submission → eligibility → judging → awards → publish
- run deadline transitions in accelerated virtual time
- show missing email/template/resource dependencies
- detect impossible stage/policy combinations
- detect judge capacity shortage before assignments

### PD-S064-B02 — Event readiness, simulation and rehearsal — detect award eligibility impossible/und… → launch certification” evidence report

- detect award eligibility impossible/undersubscribed
- detect check-in/floorplan capacity issues
- verify public-site links/media
- dry-run communication audience
- dry-run Event-as-Code plan against rehearsal copy
- stochastic dropout/no-show simulation
- deadline surge load scenario generated from current event size
- launch certification” evidence report

