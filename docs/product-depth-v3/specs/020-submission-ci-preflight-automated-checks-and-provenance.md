# PD-S020 — Submission CI, preflight, automated checks and provenance

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §20  
**Queue batches:** PD-S020-B01, PD-S020-B02, PD-S020-B03

## Completion interpretation

This specification is the canonical depth contract for §20. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `TIMELINE`
- `TYPED_CLIENT`
- `VERSION_DIFF`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | required |
| `sdk` | required |
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

The existing advanced submission CI concept can become a reusable verification engine rather than a handful of hardcoded checks.
- BASE — required field/link/artifact checks.
- BASE — repository accessible.
- BASE — demo URL resolves.
- BASE — license present when event requires it.
- BASE — deterministic pass/warn/fail categories.
- ADV — organizer-defined check pipeline.
- ADV — checks run on draft and finalization.
- ADV — async expensive checks with cached result by evidence digest.
- ADV — check explanations and remediation links.
- ADV — participant may re-run checks within rate limits.
- ADV — organizer waiver with reason and audit record.
- ADV — checks can emit structured facts consumed by eligibility rules.
- ADV — source tree constraints.
- ADV — dependency/license policy checks.
- ADV — security scanner integrations.
- ADV — artifact metadata validation.
- EXPERT — sandboxed build/test runner plugin.
- EXPERT — reproducible environment reference.
- EXPERT — provenance attestation for CI output.
- EXPERT — check version pinned to finalized evidence.
- EXPERT — historical re-evaluation clearly distinguished from original deadline result.
- PROG — checker SDK with strict input/output schema and resource limits.
- PROG — external check provider webhook with signed result.

## Batch scope

### PD-S020-B01 — Submission CI, preflight, automated checks and provenance — required field/link/artifact checks → async expensive checks with cached resu…

- required field/link/artifact checks
- repository accessible
- demo URL resolves
- license present when event requires it
- deterministic pass/warn/fail categories
- organizer-defined check pipeline
- checks run on draft and finalization
- async expensive checks with cached result by evidence digest

### PD-S020-B02 — Submission CI, preflight, automated checks and provenance — check explanations and remediation links → artifact metadata validation

- check explanations and remediation links
- participant may re-run checks within rate limits
- organizer waiver with reason and audit record
- checks can emit structured facts consumed by eligibility rules
- source tree constraints
- dependency/license policy checks
- security scanner integrations
- artifact metadata validation

### PD-S020-B03 — Submission CI, preflight, automated checks and provenance — sandboxed build/test runner plugin → external check provider webhook with si…

- sandboxed build/test runner plugin
- reproducible environment reference
- provenance attestation for CI output
- check version pinned to finalized evidence
- historical re-evaluation clearly distinguished from original deadline result
- checker SDK with strict input/output schema and resource limits
- external check provider webhook with signed result

