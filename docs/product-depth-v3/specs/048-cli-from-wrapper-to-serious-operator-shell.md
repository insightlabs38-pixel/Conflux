# PD-S048 — CLI: from wrapper to serious operator shell

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §48  
**Queue batches:** PD-S048-B01, PD-S048-B02, PD-S048-B03

## Completion interpretation

This specification is the canonical depth contract for §48. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- CLI commands are projections of canonical services. They do not add mutation semantics unavailable to API/domain services; stdout/stderr, exit status, idempotency and unknown-write outcomes are explicit.

## Canonical primitive reuse

- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `BULK_PLAN`
- `DATA_GRID`
- `EXTENSION_MANIFEST`
- `POLICY_EXPLAIN`
- `QUERY`
- `RICH_DOC`
- `VERSION_DIFF`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | not_required |
| `api` | not_required |
| `sdk` | required |
| `cli` | required |
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

The current CLI is intentionally narrow. It can become the fastest interface for technical organizers without exposing raw database mechanics.
- BASE/PROG — profile-based server/workspace selection without storing secrets insecurely.
- PROG — human table, JSON, YAML and JSONL outputs.
- PROG — predictable stdout/stderr and exit codes.
- PROG — shell completion.
- PROG — interactive selection only when a TTY is present.
- PROG — `events doctor` readiness diagnostics.
- PROG — `events diff/plan/apply` integrated with Event-as-Code.
- PROG — `participants list` with universal query syntax.
- PROG — `projects inspect` and exact submitted-evidence view.
- PROG — `judging diagnose` connectivity/coverage/conflict/workload.
- PROG — `judging plan-assignments` / `apply-assignments`.
- PROG — `judging replay` and replay diff.
- PROG — `awards explain` / `awards plan`.
- PROG — `audit tail` / filtered export.
- PROG — `bulk plan/apply` from query or CSV.
- PROG — `project description validate/render/import/export`.
- PROG — `archive verify`.
- PROG — `webhooks replay` with safety prompt.
- PROG — dry-run standard option wherever semantically possible.
- PROG — idempotency/retry behavior documented per command.
- EXPERT — local command plugins registered by extension packages.
- EXPERT — generated manpages/docs from command metadata.

## Batch scope

### PD-S048-B01 — CLI: from wrapper to serious operator shell — profile-based server/workspace selectio… → participants list with universal query…

- profile-based server/workspace selection without storing secrets insecurely
- human table, JSON, YAML and JSONL outputs
- predictable stdout/stderr and exit codes
- shell completion
- interactive selection only when a TTY is present
- `events doctor` readiness diagnostics
- `events diff/plan/apply` integrated with Event-as-Code
- `participants list` with universal query syntax

### PD-S048-B02 — CLI: from wrapper to serious operator shell — projects inspect and exact submitted-ev… → project description validate/render/imp…

- `projects inspect` and exact submitted-evidence view
- `judging diagnose` connectivity/coverage/conflict/workload
- `judging plan-assignments` / `apply-assignments`
- `judging replay` and replay diff
- `awards explain` / `awards plan`
- `audit tail` / filtered export
- `bulk plan/apply` from query or CSV
- `project description validate/render/import/export`

### PD-S048-B03 — CLI: from wrapper to serious operator shell — archive verify → generated manpages/docs from command me…

- `archive verify`
- `webhooks replay` with safety prompt
- dry-run standard option wherever semantically possible
- idempotency/retry behavior documented per command
- local command plugins registered by extension packages
- generated manpages/docs from command metadata

