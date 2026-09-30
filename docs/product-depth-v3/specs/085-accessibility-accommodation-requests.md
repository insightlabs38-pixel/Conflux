# PD-S085 — Accessibility accommodation requests

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §85  
**Queue batches:** PD-S085-B01, PD-S085-B02

## Completion interpretation

This specification is the canonical depth contract for §85. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Accommodation data is sensitive and least-privilege; aggregate planning must not unnecessarily reveal individual details.

## Canonical primitive reuse

- `ASYNC_JOB`
- `RICH_DOC`
- `ROUTER`
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

- `design/participant-my-event`
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

Accessibility should include operational accommodation, not only WCAG.

- BASE — optional accommodation request during registration.
- BASE — free-text and organizer-defined categories.
- BASE — private visibility to designated staff.
- BASE — participant can update request until a configured cutoff.
- ADV — request status and organizer note.
- ADV — accessible seating/location assignment.
- ADV — interpreter/captioning requirement.
- ADV — dietary request linkage where relevant.
- ADV — mobility/access route notes.
- ADV — session-level accommodation needs.
- ADV — individualized check-in instructions.
- EXPERT — aggregate planning counts that hide sensitive details from staff who do not need them.

**Why include:** It improves an actual participant workflow and extends accessibility beyond visual frontend compliance.

## Batch scope

### PD-S085-B01 — Accessibility accommodation requests — optional accommodation request during r… → dietary request linkage where relevant

- optional accommodation request during registration
- free-text and organizer-defined categories
- private visibility to designated staff
- participant can update request until a configured cutoff
- request status and organizer note
- accessible seating/location assignment
- interpreter/captioning requirement
- dietary request linkage where relevant

### PD-S085-B02 — Accessibility accommodation requests — mobility/access route notes → aggregate planning counts that hide sen…

- mobility/access route notes
- session-level accommodation needs
- individualized check-in instructions
- aggregate planning counts that hide sensitive details from staff who do not need them

