# PD-S044 — Governance, approvals, receipts and exceptions

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §44  
**Queue batches:** PD-S044-B01, PD-S044-B02

## Completion interpretation

This specification is the canonical depth contract for §44. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Approval policy is one canonical primitive reused by publication, deliberation, configuration and other high-impact actions. No-self-approval and threshold semantics must be consistent.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `DATA_GRID`
- `POLICY_EXPLAIN`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `THREADS`
- `TIMELINE`
- `VERSION_DIFF`

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
| `analytics` | not_required |
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

Governance is a cross-cutting differentiator: high-impact operations can be explainable and reviewable without making every action bureaucratic.
- BASE — event rules publication and acknowledgement.
- BASE — deadline exception request/grant.
- BASE — audited publication.
- ADV — generic approval policy: one approver / N-of-M / role requirement.
- ADV — no-self-approval.
- ADV — approval expiration.
- ADV — scheduled approved operation.
- ADV — change request/comments on pending operation.
- ADV — high-impact operation risk classification.
- ADV — signed/hashed receipts for submission, judging finalization and publication.
- ADV — correction workflow preserving prior public result.
- ADV — governance dashboard of pending approvals/exceptions.
- EXPERT — configurable policy requiring approval above blast-radius threshold.
- EXPERT — portable evidence package for external audit.
- PROG — operation-plan object can be consumed by UI, CLI and MCP consistently.

## Batch scope

### PD-S044-B01 — Governance, approvals, receipts and exceptions — event rules publication and acknowledge… → change request/comments on pending oper…

- event rules publication and acknowledgement
- deadline exception request/grant
- audited publication
- generic approval policy: one approver / N-of-M / role requirement
- no-self-approval
- approval expiration
- scheduled approved operation
- change request/comments on pending operation

### PD-S044-B02 — Governance, approvals, receipts and exceptions — high-impact operation risk classificati… → operation-plan object can be consumed b…

- high-impact operation risk classification
- signed/hashed receipts for submission, judging finalization and publication
- correction workflow preserving prior public result
- governance dashboard of pending approvals/exceptions
- configurable policy requiring approval above blast-radius threshold
- portable evidence package for external audit
- operation-plan object can be consumed by UI, CLI and MCP consistently

