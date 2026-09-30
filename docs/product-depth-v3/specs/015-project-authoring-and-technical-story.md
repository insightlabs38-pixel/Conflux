# PD-S015 — Project authoring and technical story

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §15  
**Queue batches:** PD-S015-B01, PD-S015-B02, PD-S015-B03, PD-S015-B04, PD-S015-B05, PD-S015-B06, PD-S015-B07, PD-S015-B08

## Completion interpretation

This specification is the canonical depth contract for §15. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Establish a canonical structured rich-document AST with stable node identities before building editor collaboration/comments/diff behavior. Markdown is an import/export/editing representation, not permission to make raw HTML the source of truth.
- Public, judge and frozen-submission renders must use the same versioned rendering pipeline and untrusted-content rules.
- Migration from the existing plain Project.description must be explicit and lossless for existing content.

## Canonical primitive reuse

- `APPROVAL`
- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `DATA_GRID`
- `EXTENSION_MANIFEST`
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `THREADS`
- `VERSION_DIFF`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | required |
| `sdk` | not_required |
| `cli` | required |
| `mcp` | required |
| `event_as_code` | not_required |
| `audit` | required |
| `webhook` | not_required |
| `archive` | required |
| `analytics` | not_required |
| `search` | required |
| `docs` | required |

## Approved-design references

- `design/project-story-editor`
- `design/public-project`
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

This deserves to become a flagship system. The current project description is plain text; a technical project deserves first-class technical writing, evidence and presentation.
- BASE — Markdown source mode with live rendered preview.
- BASE — WYSIWYM/rich editor mode backed by the same canonical document model.
- BASE — headings, lists, blockquotes, links, tables, task lists, code and images.
- BASE — GitHub-style callouts/admonitions.
- BASE — footnotes.
- BASE — syntax-highlighted fenced code blocks.
- BASE — inline and display math.
- BASE — drag/paste image uploads.
- BASE — captions and required/recommended alt text.
- BASE — draft autosave and conflict-safe revisioning.
- BASE — exact preview of public and judge rendering.
- ADV — KaTeX/MathJax-compatible LaTeX math with syntax diagnostics.
- ADV — event-controlled allowlist of safe math macros.
- ADV — equation accessibility output (MathML/text) and copy-source.
- ADV — code block filename, line numbers, highlighted lines, wrapping and copy action.
- ADV — diagram fences (e.g. Mermaid) through a constrained safe renderer.
- ADV — bibliography/citation nodes with DOI/URL metadata.
- ADV — figure/table numbering and references.
- ADV — reusable media gallery.
- ADV — image crop/focal point and responsive derivatives.
- ADV — video/provider embeds from an organizer allowlist; no arbitrary iframe by default.
- ADV — structured project metadata cards for repository, live demo, dataset, model, hardware, paper and license.
- ADV — architecture/benchmark/evaluation sections as semantic blocks.
- ADV — organizer-defined required/optional story sections.
- ADV — section-level length/media constraints.
- ADV — section visibility: public, judges, organizers, team-only.
- ADV — project content completeness score based on deterministic requirements.
- ADV — broken-link and inaccessible-media checker.
- ADV — spelling/format lint that can be advisory only.
- ADV — heading-structure/accessibility lint.
- ADV — source/render diff before final submission.
- ADV — import README.md.
- ADV — export project story to Markdown.
- ADV — pin imported repository content to a commit SHA.
- ADV — explicit sync instead of silently changing judged content when README changes.
- ADV — comments/suggestions from teammates and mentors with visibility controls.
- ADV — change history with semantic Markdown/document diff.
- ADV — restore previous draft.
- ADV — frozen judged revision separate from editable post-event story.
- ADV — compare submitted vs post-event story.
- ADV — generate static HTML/PDF/archive-safe representation.
- ADV — deterministic plain-text extraction for search/SEO.
- ADV — OpenGraph project card generation.
- EXPERT — structured AST with stable node IDs so comments survive ordinary edits.
- EXPERT — simultaneous collaborative editing as an optional layer.
- EXPERT — suggestion/track-changes mode with accept/reject.
- EXPERT — custom organizer-defined semantic node types through extension schemas.
- EXPERT — project-level localization/translated variants.
- EXPERT — content provenance manifest covering source, media digests and renderer version.
- EXPERT — exact renderer version pinned into finalized submission evidence.
- EXPERT — safe custom macro packages versioned by the event.
- EXPERT — automatic technical-content snapshot for judging replay.
- EXPERT — signed static project artifact for long-term archive.
- PROG — document schema exposed through API, not opaque HTML.
- PROG — CLI: import/export/validate/render project description.
- PROG — MCP: inspect, lint, draft patch, preview; finalization remains an explicit authorized action.
- PROG — Event configuration can define allowed content features, section schema and rendering profile.
- SECURITY — reject arbitrary script/style/event-handler HTML; prefer rendering from a structured AST.
- SECURITY — sanitize any explicitly supported raw HTML with a maintained sanitizer.
- SECURITY — validate URL schemes and remote embeds.
- SECURITY — enforce CSP as defense in depth, not as the only XSS boundary.
- SECURITY — treat participant-authored content as untrusted data in MCP/agent contexts.

## Batch scope

### PD-S015-B01 — Project authoring and technical story — Markdown source mode with live rendered… → drag/paste image uploads

- Establish canonical rich-document AST and existing-description migration scaffold
- Markdown source mode with live rendered preview
- WYSIWYM/rich editor mode backed by the same canonical document model
- headings, lists, blockquotes, links, tables, task lists, code and images
- GitHub-style callouts/admonitions
- footnotes
- syntax-highlighted fenced code blocks
- inline and display math
- drag/paste image uploads

### PD-S015-B02 — Project authoring and technical story — captions and required/recommended alt t… → diagram fences (e.g. Mermaid) through a…

- captions and required/recommended alt text
- draft autosave and conflict-safe revisioning
- exact preview of public and judge rendering
- KaTeX/MathJax-compatible LaTeX math with syntax diagnostics
- event-controlled allowlist of safe math macros
- equation accessibility output (MathML/text) and copy-source
- code block filename, line numbers, highlighted lines, wrapping and copy action
- diagram fences (e.g. Mermaid) through a constrained safe renderer

### PD-S015-B03 — Project authoring and technical story — bibliography/citation nodes with DOI/UR… → organizer-defined required/optional sto…

- bibliography/citation nodes with DOI/URL metadata
- figure/table numbering and references
- reusable media gallery
- image crop/focal point and responsive derivatives
- video/provider embeds from an organizer allowlist; no arbitrary iframe by default
- structured project metadata cards for repository, live demo, dataset, model, hardware, paper and license
- architecture/benchmark/evaluation sections as semantic blocks
- organizer-defined required/optional story sections

### PD-S015-B04 — Project authoring and technical story — section-level length/media constraints → import README.md

- section-level length/media constraints
- section visibility: public, judges, organizers, team-only
- project content completeness score based on deterministic requirements
- broken-link and inaccessible-media checker
- spelling/format lint that can be advisory only
- heading-structure/accessibility lint
- source/render diff before final submission
- import README.md

### PD-S015-B05 — Project authoring and technical story — export project story to Markdown → compare submitted vs post-event story

- export project story to Markdown
- pin imported repository content to a commit SHA
- explicit sync instead of silently changing judged content when README changes
- comments/suggestions from teammates and mentors with visibility controls
- change history with semantic Markdown/document diff
- restore previous draft
- frozen judged revision separate from editable post-event story
- compare submitted vs post-event story

### PD-S015-B06 — Project authoring and technical story — generate static HTML/PDF/archive-safe r… → project-level localization/translated v…

- generate static HTML/PDF/archive-safe representation
- deterministic plain-text extraction for search/SEO
- OpenGraph project card generation
- Harden stable rich-document node identities across edits, comments and semantic diff
- simultaneous collaborative editing as an optional layer
- suggestion/track-changes mode with accept/reject
- custom organizer-defined semantic node types through extension schemas
- project-level localization/translated variants

### PD-S015-B07 — Project authoring and technical story — content provenance manifest covering so… → MCP: inspect, lint, draft patch, previe…

- content provenance manifest covering source, media digests and renderer version
- exact renderer version pinned into finalized submission evidence
- safe custom macro packages versioned by the event
- automatic technical-content snapshot for judging replay
- signed static project artifact for long-term archive
- document schema exposed through API, not opaque HTML
- CLI: import/export/validate/render project description
- MCP: inspect, lint, draft patch, preview; finalization remains an explicit authorized action

### PD-S015-B08 — Project authoring and technical story — Event configuration can define allowed… → treat participant-authored content as u…

- Event configuration can define allowed content features, section schema and rendering profile
- reject arbitrary script/style/event-handler HTML; prefer rendering from a structured AST
- sanitize any explicitly supported raw HTML with a maintained sanitizer
- validate URL schemes and remote embeds
- enforce CSP as defense in depth, not as the only XSS boundary
- treat participant-authored content as untrusted data in MCP/agent contexts

