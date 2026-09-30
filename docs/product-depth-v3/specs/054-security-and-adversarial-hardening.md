# PD-S054 — Security and adversarial hardening

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §54  
**Queue batches:** PD-S054-B01, PD-S054-B02, PD-S054-B03

## Completion interpretation

This specification is the canonical depth contract for §54. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `EXTENSION_MANIFEST`
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`
- `RICH_DOC`
- `ROUTER`
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
| `event_as_code` | required |
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

Advanced customization raises the security bar; rich content, extensions, imports and agents need explicit trust boundaries.
- BASE — CSRF/session hardening.
- BASE — object-level authorization tests.
- BASE — secure artifact serving.
- BASE — rate limits on abuse-prone endpoints.
- ADV — content security policy.
- ADV — Trusted Types evaluation for frontend unsafe sinks.
- ADV — sanitizer centralization and version tracking.
- ADV — file/archive path traversal protections.
- ADV — image/PDF parser isolation strategy.
- ADV — SSRF controls for URL previews/checkers.
- ADV — webhook destination validation.
- ADV — secret rotation workflows.
- ADV — dependency and container scanning.
- ADV — audit alert on high-impact credential usage.
- EXPERT — fuzz Event-as-Code/import/rich-text schemas.
- EXPERT — property tests for state-machine invariants.
- EXPERT — authorization matrix generated from routes/actions and tested.
- EXPERT — extension threat model/capability sandbox.
- EXPERT — agent prompt-injection threat model and tainted-content handling.
- PROG — security-sensitive operations expose reasoned failure, never hidden bypass flags.

## Batch scope

### PD-S054-B01 — Security and adversarial hardening — CSRF/session hardening → file/archive path traversal protections

- CSRF/session hardening
- object-level authorization tests
- secure artifact serving
- rate limits on abuse-prone endpoints
- content security policy
- Trusted Types evaluation for frontend unsafe sinks
- sanitizer centralization and version tracking
- file/archive path traversal protections

### PD-S054-B02 — Security and adversarial hardening — image/PDF parser isolation strategy → property tests for state-machine invari…

- image/PDF parser isolation strategy
- SSRF controls for URL previews/checkers
- webhook destination validation
- secret rotation workflows
- dependency and container scanning
- audit alert on high-impact credential usage
- fuzz Event-as-Code/import/rich-text schemas
- property tests for state-machine invariants

### PD-S054-B03 — Security and adversarial hardening — authorization matrix generated from rou… → security-sensitive operations expose re…

- authorization matrix generated from routes/actions and tested
- extension threat model/capability sandbox
- agent prompt-injection threat model and tainted-content handling
- security-sensitive operations expose reasoned failure, never hidden bypass flags

