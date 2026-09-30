# PD-S049 — MCP / agent-native operations

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §49  
**Queue batches:** PD-S049-B01, PD-S049-B02, PD-S049-B03, PD-S049-B04

## Completion interpretation

This specification is the canonical depth contract for §49. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- MCP adds no authority. Every tool/resource/task is permission-scoped through canonical server authorization; high-impact actions are plan/approve/execute rather than direct opaque writes.
- Participant-authored text/artifacts are untrusted data, never agent instructions.

## Canonical primitive reuse

- `APPROVAL`
- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `NOTIFICATIONS`
- `POLICY_EXPLAIN`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `TIMELINE`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | not_required |
| `api` | required |
| `sdk` | required |
| `cli` | required |
| `mcp` | required |
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | required |
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
- No MCP-only authority or mutation semantics.
- No raw participant-authored content treated as trusted instructions.

## Product requirements from research

Current MCP preserves API permissions and audit boundaries, which is the correct foundation. The next step is semantic, plan-oriented tooling rather than exposing more CRUD endpoints.
- PROG — retain strict event/credential scope and server-side auth as final authority.
- PROG — tools categorized as read, propose/plan, reversible write, irreversible/high-impact write.
- PROG — hard policy enforcement independent of tool annotations.
- PROG — short-lived delegated credentials for an agent session.
- PROG — per-credential rate and operation budgets.
- PROG — resources for event summary, config schema, project evidence, audit capsule, judging diagnostics and documentation.
- PROG — skills describing multi-tool organizer workflows such as “prepare judging,” “deadline readiness,” or “publish results.”
- PROG — durable MCP tasks for assignment optimization, exports, judging replay, archive creation and large analytics.
- PROG — task progress and cancellation.
- PROG — paginated structured result sets rather than truncating important lists.
- PROG — resource links from tool results to exact evidence objects.
- PROG — semantic tool `check_deadline_readiness`.
- PROG — semantic tool `diagnose_judging_coverage`.
- PROG — semantic tool `plan_assignment_rebalance`.
- PROG — semantic tool `compare_event_configuration`.
- PROG — semantic tool `simulate_policy_change`.
- PROG — semantic tool `explain_award_selection`.
- PROG — semantic tool `prepare_results_publication`.
- PROG — semantic tool `find_submission_integrity_issues`.
- PROG — semantic tool `draft_communication_for_saved_view`.
- PROG — proposed changes returned as a durable operation plan, not immediately executed.
- PROG — human approval/step-up for high-impact execution.
- PROG — idempotency token for retryable writes.
- PROG — audit agent client identity, tool, argument names, operation plan digest and approver.
- PROG — mark participant-authored project text/artifacts as untrusted content, never system instructions.
- PROG — support safe structured extracts so an agent need not ingest arbitrary HTML.
- EXPERT — MCP Apps / richer UI only if it materially improves approval or inspection; do not duplicate the web app.
- EXPERT — OpenTelemetry trace context across MCP → API → worker.
- EXPERT — agent capability manifest generated from the same permission graph as UI/API.

## Batch scope

### PD-S049-B01 — MCP / agent-native operations — retain strict event/credential scope an… → durable MCP tasks for assignment optimi…

- retain strict event/credential scope and server-side auth as final authority
- tools categorized as read, propose/plan, reversible write, irreversible/high-impact write
- hard policy enforcement independent of tool annotations
- short-lived delegated credentials for an agent session
- per-credential rate and operation budgets
- resources for event summary, config schema, project evidence, audit capsule, judging diagnostics and documentation
- skills describing multi-tool organizer workflows such as “prepare judging,” “deadline readiness,” or “publish results
- durable MCP tasks for assignment optimization, exports, judging replay, archive creation and large analytics

### PD-S049-B02 — MCP / agent-native operations — task progress and cancellation → semantic tool simulate_policy_change

- task progress and cancellation
- paginated structured result sets rather than truncating important lists
- resource links from tool results to exact evidence objects
- semantic tool `check_deadline_readiness`
- semantic tool `diagnose_judging_coverage`
- semantic tool `plan_assignment_rebalance`
- semantic tool `compare_event_configuration`
- semantic tool `simulate_policy_change`

### PD-S049-B03 — MCP / agent-native operations — semantic tool explain_award_selection → audit agent client identity, tool, argu…

- semantic tool `explain_award_selection`
- semantic tool `prepare_results_publication`
- semantic tool `find_submission_integrity_issues`
- semantic tool `draft_communication_for_saved_view`
- proposed changes returned as a durable operation plan, not immediately executed
- human approval/step-up for high-impact execution
- idempotency token for retryable writes
- audit agent client identity, tool, argument names, operation plan digest and approver

### PD-S049-B04 — MCP / agent-native operations — mark participant-authored project text/… → agent capability manifest generated fro…

- mark participant-authored project text/artifacts as untrusted content, never system instructions
- support safe structured extracts so an agent need not ingest arbitrary HTML
- MCP Apps / richer UI only if it materially improves approval or inspection; do not duplicate the web app
- OpenTelemetry trace context across MCP → API → worker
- agent capability manifest generated from the same permission graph as UI/API

