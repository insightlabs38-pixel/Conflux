# PD-S019 — Submission lifecycle, versioning and deadline correctness

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §19  
**Queue batches:** PD-S019-B01, PD-S019-B02, PD-S019-B03

## Completion interpretation

This specification is the canonical depth contract for §19. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `AUDIT_PROVENANCE`
- `DATA_GRID`
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`
- `RICH_DOC`
- `SCHEMA_EDITOR`
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

Submission semantics are one of the places where “simple UI, rigorous backend” matters most.
- BASE — draft autosave.
- BASE — visible last-saved state.
- BASE — preflight before finalize.
- BASE — one clear finalization action.
- BASE — immutable finalized version.
- BASE — signed/hashed submission receipt.
- BASE — deadline shown in event timezone and local timezone.
- BASE — server is authoritative for deadline acceptance.
- ADV — reopen only under explicit policy/exception.
- ADV — multiple stage submissions with independent requirements.
- ADV — compare versions.
- ADV — explain why a version is judge-visible.
- ADV — finalization can freeze linked repository/artifact/content revisions.
- ADV — per-field finalization validation and direct links to fix.
- ADV — late/exception state explicit in evidence.
- ADV — idempotent finalize requests.
- ADV — queue/surge-safe finalization receipt even if downstream processing is deferred.
- EXPERT — cryptographic manifest of every judge-visible evidence element.
- EXPERT — deterministic reconstruction of a submission as-of deadline.
- EXPERT — dispute/review workflow for timestamp or evidence mismatch.
- PROG — submission state machine is introspectable, never inferred from scattered timestamps.

## Batch scope

### PD-S019-B01 — Submission lifecycle, versioning and deadline correctness — draft autosave → server is authoritative for deadline ac…

- draft autosave
- visible last-saved state
- preflight before finalize
- one clear finalization action
- immutable finalized version
- signed/hashed submission receipt
- deadline shown in event timezone and local timezone
- server is authoritative for deadline acceptance

### PD-S019-B02 — Submission lifecycle, versioning and deadline correctness — reopen only under explicit policy/excep… → idempotent finalize requests

- reopen only under explicit policy/exception
- multiple stage submissions with independent requirements
- compare versions
- explain why a version is judge-visible
- finalization can freeze linked repository/artifact/content revisions
- per-field finalization validation and direct links to fix
- late/exception state explicit in evidence
- idempotent finalize requests

### PD-S019-B03 — Submission lifecycle, versioning and deadline correctness — queue/surge-safe finalization receipt e… → submission state machine is introspecta…

- queue/surge-safe finalization receipt even if downstream processing is deferred
- cryptographic manifest of every judge-visible evidence element
- deterministic reconstruction of a submission as-of deadline
- dispute/review workflow for timestamp or evidence mismatch
- submission state machine is introspectable, never inferred from scattered timestamps

