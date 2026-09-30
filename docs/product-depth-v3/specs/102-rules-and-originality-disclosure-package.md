# PD-S102 — Rules and originality disclosure package

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §102  
**Queue batches:** PD-S102-B01, PD-S102-B02

## Completion interpretation

This specification is the canonical depth contract for §102. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Originality/prior-work/AI-use disclosure is structured participant evidence. Similarity tools are review signals only, never automatic misconduct decisions.

## Canonical primitive reuse

- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`
- `RICH_DOC`
- `THREADS`
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
| `webhook` | not_required |
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
- No IDE/keystroke/screen surveillance and no automatic misconduct verdict from similarity tools.

## Product requirements from research

The existing eligibility system can absorb a practical challenge that has become more important with AI tools and reuse.

- BASE — participant explicitly declares whether project work began before the allowed window.
- BASE — framework/library/tool disclosure.
- BASE — AI-tool usage disclosure when event requires it.
- BASE — third-party assets/data/API disclosure.
- BASE — cross-submission/cross-posting declaration.
- BASE — license/permission acknowledgement.
- ADV — structured “what existed before vs what we built during the event.”
- ADV — per-component provenance note.
- ADV — pre-existing repository commit/reference.
- ADV — organizer clarification request.
- ADV — disclosure frozen with submission.
- ADV — check disclosed tools against track/sponsor eligibility rules.
- EXPERT — optional code/repository diff evidence from a declared starting commit.
- EXPERT — plagiarism/similarity scanners only as review signals, never automatic guilt.
- DO NOT BUILD — invasive developer surveillance or IDE monitoring.

**Why include:** MLH's current rules explicitly discuss prior work, frameworks and AI disclosure. A structured workflow is better than burying this in README text.

## Batch scope

### PD-S102-B01 — Rules and originality disclosure package — participant explicitly declares whether… → per-component provenance note

- participant explicitly declares whether project work began before the allowed window
- framework/library/tool disclosure
- AI-tool usage disclosure when event requires it
- third-party assets/data/API disclosure
- cross-submission/cross-posting declaration
- license/permission acknowledgement
- structured “what existed before vs what we built during the event
- per-component provenance note

### PD-S102-B02 — Rules and originality disclosure package — pre-existing repository commit/reference → plagiarism/similarity scanners only as…

- pre-existing repository commit/reference
- organizer clarification request
- disclosure frozen with submission
- check disclosed tools against track/sponsor eligibility rules
- optional code/repository diff evidence from a declared starting commit
- plagiarism/similarity scanners only as review signals, never automatic guilt

