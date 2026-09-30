# PD-S118 — Saved operational playbooks

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §118  
**Queue batches:** PD-S118-B01, PD-S118-B02

## Completion interpretation

This specification is the canonical depth contract for §118. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Playbooks link canonical actions/views/approvals; they are not a second free-form workflow engine.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `NOTIFICATIONS`
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
| `archive` | not_required |
| `analytics` | not_required |
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
- No second generic no-code workflow engine.

## Product requirements from research

For recurring organizers, capture proven procedures without building a generic workflow engine.

Examples:

- “open registration”;
- “one week before event”;
- “doors open”;
- “submission deadline”;
- “start judging”;
- “judge no-show”;
- “publish winners”;
- “event closeout.”

A playbook can include:

- checklist tasks;
- links to Conflux actions/views;
- draft communications;
- required approvals;
- responsible roles;
- expected evidence.

**Why include:** Converts tacit organizer knowledge into reusable operating procedure.

## Batch scope

### PD-S118-B01 — Saved operational playbooks — Operational playbook preset: open regis… → Operational playbook preset: event clos…

- Operational playbook preset: open registration
- Operational playbook preset: one week before event
- Operational playbook preset: doors open
- Operational playbook preset: submission deadline
- Operational playbook preset: start judging
- Operational playbook preset: judge no-show
- Operational playbook preset: publish winners
- Operational playbook preset: event closeout

### PD-S118-B02 — Saved operational playbooks — Operational playbook element: checklist… → Operational playbook element: expected…

- Operational playbook element: checklist tasks
- Operational playbook element: links to Conflux actions/views
- Operational playbook element: draft communications
- Operational playbook element: required approvals
- Operational playbook element: responsible roles
- Operational playbook element: expected evidence

