# PD-S130 — Human-readable explanations everywhere a solver/policy decides something

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §130  
**Queue batches:** PD-S130-B01

## Completion interpretation

This specification is the canonical depth contract for §130. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Build a structured deterministic explanation model with reason codes/source facts/redaction. The listed sentences are acceptance adapters/examples, not hardcoded explanation logic.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `POLICY_EXPLAIN`
- `RICH_DOC`
- `ROUTER`

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

Not giant proofs. Useful explanations:

- “Assigned because this judge matches AI track, has capacity, and no conflict.”
- “Project cannot enter award because challenge opt-in was not finalized.”
- “Event-as-Code apply would remove 3 unmanaged pages only with prune.”
- “Participant is blocked from check-in because required waiver v3 is incomplete.”
- “This judge route is infeasible because two assigned projects overlap the same 10-minute window.”

**Outcome:** algorithmic depth creates trust instead of opacity.

## Batch scope

### PD-S130-B01 — Deterministic explanations — assignment, award, config-plan, check-in and routing adapters

- Human-readable explanation: Assigned because this judge matches AI track, has capacity, and no conflict
- Human-readable explanation: Project cannot enter award because challenge opt-in was not finalized
- Human-readable explanation: Event-as-Code apply would remove 3 unmanaged pages only with prune
- Human-readable explanation: Participant is blocked from check-in because required waiver v3 is incomplete
- Human-readable explanation: This judge route is infeasible because two assigned projects overlap the same 10-minute window

