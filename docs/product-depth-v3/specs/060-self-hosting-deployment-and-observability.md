# PD-S060 — Self-hosting, deployment and observability

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §60  
**Queue batches:** PD-S060-B01, PD-S060-B02, PD-S060-B03

## Completion interpretation

This specification is the canonical depth contract for §60. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

## Canonical primitive reuse

- `ASYNC_JOB`
- `POLICY_EXPLAIN`
- `RICH_DOC`
- `SCHEMA_EDITOR`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | not_required |
| `api` | required |
| `sdk` | not_required |
| `cli` | required |
| `mcp` | not_required |
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

## Product requirements from research

The self-hosted experience should punch above normal OSS projects.
- BASE — one-command Compose remains the easy default.
- BASE — health/readiness endpoints.
- BASE — clear upgrade/backup/restore docs.
- ADV — external PostgreSQL/S3/Valkey deployment profile.
- ADV — structured logs with correlation IDs.
- ADV — metrics endpoint / dashboards.
- ADV — OpenTelemetry traces.
- ADV — worker queue visibility.
- ADV — DB migration preflight.
- ADV — backup verification, not just backup creation.
- ADV — restore rehearsal command.
- ADV — release compatibility checker.
- ADV — admin “system doctor” page.
- EXPERT — Helm chart only after operational demand.
- EXPERT — HA reference architecture.
- EXPERT — rolling-upgrade compatibility policy.
- EXPERT — storage/provider conformance suite.
- PROG — diagnostics bundle redacts secrets and can be attached to bug reports.

## Batch scope

### PD-S060-B01 — Self-hosting, deployment and observability — one-command Compose remains the easy de… → worker queue visibility

- one-command Compose remains the easy default
- health/readiness endpoints
- clear upgrade/backup/restore docs
- external PostgreSQL/S3/Valkey deployment profile
- structured logs with correlation IDs
- metrics endpoint / dashboards
- OpenTelemetry traces
- worker queue visibility

### PD-S060-B02 — Self-hosting, deployment and observability — DB migration preflight → rolling-upgrade compatibility policy

- DB migration preflight
- backup verification, not just backup creation
- restore rehearsal command
- release compatibility checker
- admin “system doctor” page
- Helm chart only after operational demand
- HA reference architecture
- rolling-upgrade compatibility policy

### PD-S060-B03 — Self-hosting, deployment and observability — storage/provider conformance suite → diagnostics bundle redacts secrets and…

- storage/provider conformance suite
- diagnostics bundle redacts secrets and can be attached to bug reports

