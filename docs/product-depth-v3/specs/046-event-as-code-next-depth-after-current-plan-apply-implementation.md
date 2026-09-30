# PD-S046 — Event-as-Code: next depth after current plan/apply implementation

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §46  
**Queue batches:** PD-S046-B01, PD-S046-B02, PD-S046-B03, PD-S046-B04, PD-S046-B05

## Completion interpretation

This specification is the canonical depth contract for §46. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Event-as-Code operates only on configuration scope, never participant/runtime truth. Plan/apply remains atomic/idempotent with reviewed-digest protection.
- Typed resources, ownership, modules and overlays must preserve stable logical identity across rename/refactor/import.

## Canonical primitive reuse

- `APPROVAL`
- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `DATA_GRID`
- `EXTENSION_MANIFEST`
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
| `sdk` | required |
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

Conflux already has deterministic export, validation, semantic plan, digest-guarded atomic apply, safe pruning and configuration/runtime separation. The next layer should focus on composition, ownership, refactoring and collaboration rather than merely adding more YAML.
- BASE/PROG — explicit `apiVersion`, `kind`, `metadata`, `spec` conventions for resource-like documents.
- PROG — split optional monolithic event document into typed logical resources: Event, Track, Stage, Form, Policy, Rubric, Award, Page, Theme, Integration.
- PROG — stable logical names/IDs distinct from display names.
- PROG — generated JSON Schema for editor autocomplete and CI.
- PROG — `conflux fmt` canonical formatting.
- PROG — `conflux schema` and local validation without server where possible.
- PROG — cross-resource reference validation.
- PROG — semantic lint rules.
- PROG — plan risk levels and blast-radius summary.
- PROG — saved plan artifact so apply executes exactly the reviewed plan.
- PROG — signed plan/approval artifact for protected events.
- PROG — semantic `moved`/rename declarations preserving live identity across refactors.
- PROG — import/adopt an existing UI-created object into code ownership without recreation.
- PROG — detach/unmanage an object without deleting it.
- PROG — explicit prune scopes/apply sets; never infer global ownership.
- PROG — drift detection between declared and live configuration.
- PROG — field ownership: UI, Event-as-Code and extensions can intentionally own different fields without endless drift.
- PROG — ownership conflict diagnostics before apply.
- PROG — modules/packages with typed inputs and outputs.
- PROG — module version constraints and lock file.
- PROG — module registry/local module library.
- PROG — base configuration + overlays for yearly edition, venue, sponsor pack or environment.
- PROG — secrets represented as references, never serialized into normal event config.
- PROG — preview event generated from pull request / branch.
- PROG — CI check: validate, plan, policy test and visual page snapshot.
- PROG — protected apply requiring reviewer approval.
- PROG — scheduled apply / activation time.
- PROG — config unit tests with synthetic input values.
- PROG — generated dependency graph.
- PROG — `conflux explain <resource.field>` showing current value, owner, source/default and dependents.
- PROG — schema-version migration with deterministic upgrader.
- PROG — downgrade/compatibility report.
- PROG — extension-defined config kinds using registered schemas and validators.
- PROG — local documentation generation from the event config.
- PROG — configuration history can generate a reverse/rollback proposal where semantically safe.
- EXPERT — policy-as-code gates on configuration plans.
- EXPERT — change windows/freezes preventing risky config mutation during deadline/judging unless break-glass procedure is used.

## Batch scope

### PD-S046-B01 — Event-as-Code: next depth after current plan/apply implementation — explicit apiVersion, kind, metadata, sp… → semantic lint rules

- explicit `apiVersion`, `kind`, `metadata`, `spec` conventions for resource-like documents
- split optional monolithic event document into typed logical resources: Event, Track, Stage, Form, Policy, Rubric, Award, Page, Th…
- stable logical names/IDs distinct from display names
- generated JSON Schema for editor autocomplete and CI
- `conflux fmt` canonical formatting
- `conflux schema` and local validation without server where possible
- cross-resource reference validation
- semantic lint rules

### PD-S046-B02 — Event-as-Code: next depth after current plan/apply implementation — plan risk levels and blast-radius summa… → drift detection between declared and li…

- plan risk levels and blast-radius summary
- saved plan artifact so apply executes exactly the reviewed plan
- signed plan/approval artifact for protected events
- semantic `moved`/rename declarations preserving live identity across refactors
- import/adopt an existing UI-created object into code ownership without recreation
- detach/unmanage an object without deleting it
- explicit prune scopes/apply sets; never infer global ownership
- drift detection between declared and live configuration

### PD-S046-B03 — Event-as-Code: next depth after current plan/apply implementation — field ownership: UI, Event-as-Code and… → preview event generated from pull reque…

- field ownership: UI, Event-as-Code and extensions can intentionally own different fields without endless drift
- ownership conflict diagnostics before apply
- modules/packages with typed inputs and outputs
- module version constraints and lock file
- module registry/local module library
- base configuration + overlays for yearly edition, venue, sponsor pack or environment
- secrets represented as references, never serialized into normal event config
- preview event generated from pull request / branch

### PD-S046-B04 — Event-as-Code: next depth after current plan/apply implementation — CI check: validate, plan, policy test a… → downgrade/compatibility report

- CI check: validate, plan, policy test and visual page snapshot
- protected apply requiring reviewer approval
- scheduled apply / activation time
- config unit tests with synthetic input values
- generated dependency graph
- `conflux explain <resource.field>` showing current value, owner, source/default and dependents
- schema-version migration with deterministic upgrader
- downgrade/compatibility report

### PD-S046-B05 — Event-as-Code: next depth after current plan/apply implementation — extension-defined config kinds using re… → change windows/freezes preventing risky…

- extension-defined config kinds using registered schemas and validators
- local documentation generation from the event config
- configuration history can generate a reverse/rollback proposal where semantically safe
- policy-as-code gates on configuration plans
- change windows/freezes preventing risky config mutation during deadline/judging unless break-glass procedure is used

