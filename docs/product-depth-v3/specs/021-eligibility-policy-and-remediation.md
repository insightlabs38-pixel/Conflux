# PD-S021 — Eligibility, policy and remediation

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §21  
**Queue batches:** PD-S021-B01, PD-S021-B02, PD-S021-B03

## Completion interpretation

This specification is the canonical depth contract for §21. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Eligibility rules consume structured facts and policy versions; they must not scrape rendered UI text. Waivers/exceptions are explicit audited state, never silent bypasses.

## Canonical primitive reuse

- `APPROVAL`
- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `DATA_GRID`
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`
- `RICH_DOC`
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

Conflux already has policy gates, exceptions and eligibility remediation. The next level is a transparent rules system that can be simulated and explained.
- BASE — eligibility status and concrete findings.
- BASE — participant remediation/resubmission.
- BASE — organizer approve/request changes/reject.
- BASE — immutable decision history.
- ADV — declarative eligibility rule sets.
- ADV — rules consume structured facts rather than scraping display text.
- ADV — rule severity: error/warning/info.
- ADV — rule version pinned to decisions.
- ADV — “why did this fail?” trace.
- ADV — “who would be affected if this rule changed?” simulation.
- ADV — policy debugger with representative test cases.
- ADV — exception grants with scope, expiration and reason.
- ADV — reusable policy bundles.
- ADV — cohort/track/stage-specific rules.
- ADV — scheduled rule activation with impact preview.
- EXPERT — policy static analyzer for contradictory/unreachable conditions.
- EXPERT — property-style tests for policy invariants.
- EXPERT — decision appeal/review pipeline.
- PROG — policy explain/simulate endpoints used by UI/CLI/MCP.

## Batch scope

### PD-S021-B01 — Eligibility, policy and remediation — eligibility status and concrete findings → rule version pinned to decisions

- eligibility status and concrete findings
- participant remediation/resubmission
- organizer approve/request changes/reject
- immutable decision history
- declarative eligibility rule sets
- rules consume structured facts rather than scraping display text
- rule severity: error/warning/info
- rule version pinned to decisions

### PD-S021-B02 — Eligibility, policy and remediation — why did this fail?” trace → policy static analyzer for contradictor…

- why did this fail?” trace
- who would be affected if this rule changed?” simulation
- policy debugger with representative test cases
- exception grants with scope, expiration and reason
- reusable policy bundles
- cohort/track/stage-specific rules
- scheduled rule activation with impact preview
- policy static analyzer for contradictory/unreachable conditions

### PD-S021-B03 — Eligibility, policy and remediation — property-style tests for policy invaria… → policy explain/simulate endpoints used…

- property-style tests for policy invariants
- decision appeal/review pipeline
- policy explain/simulate endpoints used by UI/CLI/MCP

