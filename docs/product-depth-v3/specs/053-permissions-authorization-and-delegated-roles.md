# PD-S053 — Permissions, authorization and delegated roles

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §53  
**Queue batches:** PD-S053-B01, PD-S053-B02

## Completion interpretation

This specification is the canonical depth contract for §53. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Authorization is explainable and server authoritative. Custom roles/bundles compose existing permission checks rather than adding UI-only restrictions.

## Canonical primitive reuse

- `APPROVAL`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `BULK_PLAN`
- `EXTENSION_MANIFEST`
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`
- `RICH_DOC`

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

The role model can grow without becoming an enterprise IAM project by adding composable scopes and policy diagnostics.
- BASE — participant/judge/mentor/volunteer/organizer/admin roles.
- BASE — event/workspace scope obvious in UI.
- ADV — custom limited organizer roles.
- ADV — permission bundles.
- ADV — track/stage-specific permissions.
- ADV — sponsor-scoped access.
- ADV — read vs decide vs publish separation.
- ADV — temporary role grant with expiration.
- ADV — service/API credentials bound to actor and scope.
- ADV — permission explanation: “why can/can't this user do X?”
- ADV — preview permissions as role without impersonating credentials.
- ADV — bulk role assignment with dry-run.
- EXPERT — attribute/policy rules only where role bundles are insufficient.
- EXPERT — break-glass operation with explicit audit.
- PROG — extension capabilities must map into the same authorization framework.

## Batch scope

### PD-S053-B01 — Permissions, authorization and delegated roles — participant/judge/mentor/volunteer/orga… → temporary role grant with expiration

- participant/judge/mentor/volunteer/organizer/admin roles
- event/workspace scope obvious in UI
- custom limited organizer roles
- permission bundles
- track/stage-specific permissions
- sponsor-scoped access
- read vs decide vs publish separation
- temporary role grant with expiration

### PD-S053-B02 — Permissions, authorization and delegated roles — service/API credentials bound to actor… → extension capabilities must map into th…

- service/API credentials bound to actor and scope
- permission explanation: “why can/can't this user do X?
- preview permissions as role without impersonating credentials
- bulk role assignment with dry-run
- attribute/policy rules only where role bundles are insufficient
- break-glass operation with explicit audit
- extension capabilities must map into the same authorization framework

