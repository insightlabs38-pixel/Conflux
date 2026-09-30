# PD-S007 — Event creation, setup and lifecycle

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §7  
**Queue batches:** PD-S007-B01, PD-S007-B02, PD-S007-B03

## Completion interpretation

This specification is the canonical depth contract for §7. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `ASYNC_JOB`
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `TIMELINE`

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

Conflux already has events, stages, policies, temporal gates, templates and status transitions. The depth opportunity is to make setup both simpler for normal events and substantially more expressive for unusual ones.
- BASE — Guided event creation from strong presets: weekend hackathon, online hackathon, demo day, internal innovation challenge, research competition.
- BASE — Readiness checklist derived from actual configured invariants, not a hand-maintained checklist.
- BASE — Draft/open/frozen/judging/results/archived state presented as a clear lifecycle with allowed next actions.
- BASE — Calendar-aware deadline editor with timezone preview and DST warnings.
- BASE — Human-readable dependency warnings when a stage/date change would invalidate submissions, assignments or publication.
- BASE — Clone last year's event with explicit choices for what transfers and what must not.
- ADV — Arbitrary stage graph visualization with branches, merges and external qualification nodes.
- ADV — Stage-specific team rules, submission requirements, visibility and judging methods.
- ADV — Conditional advancement based on scores, eligibility, manual approval, external result, or composite rules.
- ADV — Stage transition simulator using current participant/project data.
- ADV — Event-wide “what changes if I…” impact preview.
- ADV — Scheduled state transitions with approval gates.
- ADV — Rehearsal mode that runs event workflow against synthetic participants without affecting production records.
- EXPERT — Multiple parallel competitions/tracks sharing registration but diverging in workflow.
- EXPERT — Cohort-specific calendars or deadlines with explicit exception precedence.
- EXPERT — Lifecycle invariants as declarative rules with explanation traces.
- PROG — Every lifecycle/config mutation available as semantic plan + apply, not raw model patching.
- PROG — Event graph export as Mermaid/DOT/JSON for docs and review.

## Batch scope

### PD-S007-B01 — Event creation, setup and lifecycle — Guided event creation from strong prese… → Stage-specific team rules, submission r…

- Guided event creation from strong presets: weekend hackathon, online hackathon, demo day, internal innovation challenge, research…
- Readiness checklist derived from actual configured invariants, not a hand-maintained checklist
- Draft/open/frozen/judging/results/archived state presented as a clear lifecycle with allowed next actions
- Calendar-aware deadline editor with timezone preview and DST warnings
- Human-readable dependency warnings when a stage/date change would invalidate submissions, assignments or publication
- Clone last year's event with explicit choices for what transfers and what must not
- Arbitrary stage graph visualization with branches, merges and external qualification nodes
- Stage-specific team rules, submission requirements, visibility and judging methods

### PD-S007-B02 — Event creation, setup and lifecycle — Conditional advancement based on scores… → Lifecycle invariants as declarative rul…

- Conditional advancement based on scores, eligibility, manual approval, external result, or composite rules
- Stage transition simulator using current participant/project data
- Event-wide “what changes if I…” impact preview
- Scheduled state transitions with approval gates
- Rehearsal mode that runs event workflow against synthetic participants without affecting production records
- Multiple parallel competitions/tracks sharing registration but diverging in workflow
- Cohort-specific calendars or deadlines with explicit exception precedence
- Lifecycle invariants as declarative rules with explanation traces

### PD-S007-B03 — Event creation, setup and lifecycle — Every lifecycle/config mutation availab… → Event graph export as Mermaid/DOT/JSON…

- Every lifecycle/config mutation available as semantic plan + apply, not raw model patching
- Event graph export as Mermaid/DOT/JSON for docs and review

