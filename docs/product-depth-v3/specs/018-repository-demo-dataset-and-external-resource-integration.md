# PD-S018 — Repository, demo, dataset and external-resource integration

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §18  
**Queue batches:** PD-S018-B01, PD-S018-B02

## Completion interpretation

This specification is the canonical depth contract for §18. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `EXTENSION_MANIFEST`
- `POLICY_EXPLAIN`
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
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | not_required |
| `archive` | required |
| `analytics` | not_required |
| `search` | required |
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

Technical projects often live outside the platform; Conflux should make those references trustworthy and useful rather than merely accepting URLs.
- BASE — repository and demo URL fields.
- BASE — URL reachability check.
- BASE — repository provider detection.
- ADV — GitHub/GitLab authorization and repository picker.
- ADV — pin repository to submission commit.
- ADV — capture default branch, commit, tag and repository metadata.
- ADV — capture license file and primary languages.
- ADV — demo endpoint screenshot/health result.
- ADV — dataset/model registry links.
- ADV — DOI/arXiv/paper metadata.
- ADV — hardware/BOM links.
- ADV — organizer allowlist/denylist provider policy.
- EXPERT — source archive generated from pinned commit.
- EXPERT — signed provider webhook confirming commit existence at deadline.
- EXPERT — integration-independent canonical repository evidence schema.
- PROG — provider adapters as extension points, not hardcoded UI branches.

## Batch scope

### PD-S018-B01 — Repository, demo, dataset and external-resource integration — repository and demo URL fields → demo endpoint screenshot/health result

- repository and demo URL fields
- URL reachability check
- repository provider detection
- GitHub/GitLab authorization and repository picker
- pin repository to submission commit
- capture default branch, commit, tag and repository metadata
- capture license file and primary languages
- demo endpoint screenshot/health result

### PD-S018-B02 — Repository, demo, dataset and external-resource integration — dataset/model registry links → provider adapters as extension points,…

- dataset/model registry links
- DOI/arXiv/paper metadata
- hardware/BOM links
- organizer allowlist/denylist provider policy
- source archive generated from pinned commit
- signed provider webhook confirming commit existence at deadline
- integration-independent canonical repository evidence schema
- provider adapters as extension points, not hardcoded UI branches

