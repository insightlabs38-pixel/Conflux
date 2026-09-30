# PD-S017 — Artifact upload, storage and evidence

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §17  
**Queue batches:** PD-S017-B01, PD-S017-B02, PD-S017-B03, PD-S017-B04

## Completion interpretation

This specification is the canonical depth contract for §17. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

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
- `DATA_GRID`
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`
- `RICH_DOC`
- `SCHEMA_EDITOR`
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

- `design/judge-review`
- `design/project-story-editor`
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

Artifacts are not merely files; in a competition they are evidence with lifecycle, integrity and access semantics.
- BASE — multi-file upload with progress and retry.
- BASE — drag/drop/paste.
- BASE — file type/size policy shown before upload.
- BASE — checksum recorded.
- BASE — safe download names and content disposition.
- BASE — image/PDF/text/source/JSON/CSV previews.
- BASE — inaccessible preview never blocks secure download if policy allows.
- ADV — folders/collections for evidence organization.
- ADV — labels such as demo, paper, dataset, slides, source snapshot, logs.
- ADV — virus/malware scanning hook.
- ADV — archive inspection without blindly extracting unsafe paths.
- ADV — media transcoding/thumbnail derivatives.
- ADV — duplicate/deduplicated upload detection.
- ADV — expiring external artifact reference with health check.
- ADV — object drift detection.
- ADV — immutable frozen artifact set at submission finalization.
- ADV — participant can see exact judge-visible artifact set.
- ADV — artifact replacement history before finalization.
- EXPERT — provenance graph linking source commit → build → artifact → submission version.
- EXPERT — content-addressed artifact identity where practical.
- EXPERT — configurable retention tier by artifact class.
- EXPERT — signed artifact manifest.
- EXPERT — long-term archive package with media metadata.
- PROG — storage adapters with conformance tests.
- PROG — artifact events emitted through webhooks/outbox.

## Batch scope

### PD-S017-B01 — Artifact upload, storage and evidence — multi-file upload with progress and ret… → folders/collections for evidence organi…

- multi-file upload with progress and retry
- drag/drop/paste
- file type/size policy shown before upload
- checksum recorded
- safe download names and content disposition
- image/PDF/text/source/JSON/CSV previews
- inaccessible preview never blocks secure download if policy allows
- folders/collections for evidence organization

### PD-S017-B02 — Artifact upload, storage and evidence — labels such as demo, paper, dataset, sl… → immutable frozen artifact set at submis…

- labels such as demo, paper, dataset, slides, source snapshot, logs
- virus/malware scanning hook
- archive inspection without blindly extracting unsafe paths
- media transcoding/thumbnail derivatives
- duplicate/deduplicated upload detection
- expiring external artifact reference with health check
- object drift detection
- immutable frozen artifact set at submission finalization

### PD-S017-B03 — Artifact upload, storage and evidence — participant can see exact judge-visible… → storage adapters with conformance tests

- participant can see exact judge-visible artifact set
- artifact replacement history before finalization
- provenance graph linking source commit → build → artifact → submission version
- content-addressed artifact identity where practical
- configurable retention tier by artifact class
- signed artifact manifest
- long-term archive package with media metadata
- storage adapters with conformance tests

### PD-S017-B04 — Artifact upload, storage and evidence — artifact events emitted through webhooks/outbox

- artifact events emitted through webhooks/outbox

