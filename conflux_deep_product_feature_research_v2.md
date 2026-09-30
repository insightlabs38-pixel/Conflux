# Conflux Deep Product Surface & Feature Expansion Research

**Date:** 2026-09-29  
**Purpose:** Define the plausible upper bound of Conflux as an unusually advanced, customizable, self-hostable hackathon and technical-competition operating system—without sacrificing the quality or simplicity of its default experience.

---

## Executive thesis

Conflux should not optimize for “having more features than Devpost.” That target is too shallow.

The stronger target is:

> **The most advanced and customizable hackathon / technical-competition software that is still excellent in its base configuration.**

That implies four simultaneous standards:

1. **Base-state excellence.** A normal organizer can create and run a conventional hackathon without understanding the advanced architecture.
2. **Depth, not checkbox breadth.** Existing capabilities should become complete systems with diagnostics, history, permissions, automation, imports/exports, bulk operations, edge-case handling, and serious UX.
3. **One coherent platform.** UI, API, CLI, MCP, Event-as-Code, audit, archives, search, analytics, and extensions should operate over the same domain semantics rather than becoming parallel products.
4. **Professional product quality.** The interface must look deliberately designed, not generated, scaffolded, or “AI slop.” Advanced capabilities should increase power without degrading the visual hierarchy.

The current repository is already far beyond a basic hackathon CRUD application. The core, Stretch, Very-Stretch, and Post-Very-Stretch work cover staged event lifecycles, policies, submissions, sophisticated judging, eligibility/remediation, deliberation, on-site operations, physical judge routing, Event-as-Code, deterministic judging replay, audit capsules, artifact inspection, sponsor resources, mentorship, governance, SSO, MCP, portfolios, continuation, and performance hardening. The correct next question is therefore not “what major feature category is missing?” but **“how deep can each category become, and which shared primitives let that depth compound?”**

---

## Research inputs and adjacent systems

This study uses Conflux's current repository as the floor, then borrows *patterns*, not product clones, from several mature adjacent systems:

- **Devfolio Organizer Dashboard (2026):** dense application review, keyboard-first decisions, undo, URL state, live collaboration, server-state architecture.
- **TAIKAI:** rich hackathon submissions, voting, messaging, livestreaming, and a native MCP surface.
- **OpenReview:** conflicts, reviewer bids, expertise/affinity, automatic matching, multiple matching runs, quotas, review stages, rebuttal, meta-review, decision workflows.
- **HotCRP:** expressive search, bulk assignment, tracks/permissions, review rounds, tags, formulas, discussion ordering, review-quality ratings.
- **pretix:** independent check-in lists, safe scanning APIs, offline sync, badges, access control, attendance operations.
- **Terraform:** plan/apply, saved plans, import, idempotency, modules, refactoring/move semantics, drift.
- **Kubernetes/Kustomize:** typed declarative resources, schema validation, field ownership, dry-run, overlays, extension resource schemas.
- **Shopify theme architecture:** sections, nested blocks, schemas, presets, defaults, locales, app/extensibility blocks.
- **Linear/GitHub Projects:** URL-reflected filters, nested AND/OR filters, saved views, grouping, board/list parity, command palette, keyboard selection and bulk actions.
- **GitHub Markdown + MathJax:** a predictable technical-markup baseline with math, callouts, code, footnotes, and accessible rendering.
- **OWASP guidance:** structured rendering, safe sinks, sanitization where HTML is unavoidable, and CSP as defense-in-depth.
- **Modern MCP:** resources, skills, permissioned tools, structured outputs, and durable tasks for long-running operations.

The recommendation throughout is to adopt the *underlying product primitive* where useful, not to reproduce unrelated complexity.

---

## Feature-status vocabulary

- **BASE** — should feel obvious and polished to a conventional organizer/participant.
- **ADV** — advanced option exposed through progressive disclosure.
- **EXPERT** — specialist capability for large, unusual, technical, or high-stakes events.
- **PROG** — should also have a coherent programmable representation (API, CLI, MCP, Event-as-Code, extension SDK, or several).
- **OPTIONAL** — valuable, but should not burden the default installation or experience.

---

# Part I — Product laws

## 1. Base experience must remain smaller than the platform

A platform can contain 500 capabilities while a new organizer sees only 15 decisions.

- BASE: event creation starts from a high-quality preset with event name, dates, registration, team rules, project requirements, judging method, awards, and publish controls.
- BASE: advanced configuration stays collapsed until a feature requiring it is enabled.
- BASE: sane defaults are real defaults, not placeholder values requiring organizer cleanup.
- BASE: disabled systems disappear from navigation rather than presenting empty tabs.
- BASE: one canonical “event readiness” surface explains what is missing before launch.
- ADV: organizers can progressively switch from presets to custom workflows.
- EXPERT: every default can eventually be overridden where domain invariants permit.
- PROG: defaults and derived values are queryable so automation never has to reverse-engineer UI behavior.
- PROG: generated configuration includes explicit values only when necessary; inherited defaults remain legible.
- BASE: destructive or high-impact operations show consequences, not generic “Are you sure?” dialogs.

## 2. Feature depth should compound through shared primitives

Before adding hundreds of bespoke screens, Conflux should build reusable primitives that make the next 100 features cheaper:

- Universal entity query/filter engine.
- Saved views and sharable view URLs.
- Configurable dense data-grid primitive.
- Bulk-operation planner with dry-run, impact preview, execution receipt, retry and rollback/compensation semantics where possible.
- Generic async-job/task model with progress, cancellation, logs, artifacts and durable results.
- Generic approval/gate model.
- Generic comments/notes/mentions/thread model with explicit visibility.
- Generic event timeline/scheduling primitive.
- Generic schema-driven form/config editor.
- Generic rich technical content renderer/editor.
- Generic file/artifact preview pipeline.
- Generic notification/subscription preference model.
- Generic version/diff model for mutable configuration and content.
- Generic policy/explanation model.
- Generic audit provenance envelope.
- Generic extension manifest/capability model.
- Generic “preview as role / as of time / as frozen version” infrastructure.

## 3. A cross-surface completeness contract

For every important domain feature, consider whether it needs all of the following:

- Stable public identity and clear lifecycle.
- Backend validation and invariants.
- Authorization and scope rules.
- Audit events.
- Idempotency/concurrency semantics.
- REST representation.
- Generated SDK representation.
- Search/filter/index fields.
- Base UI.
- Advanced UI.
- Bulk-operation support.
- CLI inspect/action support when useful.
- MCP inspect/plan/action support when useful.
- Event-as-Code representation if it is configuration, not runtime participant data.
- Webhook/outbox events.
- Archive/import/export representation.
- Analytics dimensions.
- Retention/privacy semantics.
- Extension hooks.
- Version/migration behavior.
- Test-fixture/scenario support.

A feature is “deep” when these pieces compose naturally, not when it has a long settings page.

---

# Part II — UI and interaction quality bar

## 4. Visual direction: professional, clean, compact, deliberate

Conflux should explicitly reject several common low-quality SaaS/AI-generated UI patterns.

### Default visual language

- BASE: neutral, content-first application shell.
- BASE: modest border radii; avoid turning every region into a giant rounded card.
- BASE: controlled use of elevation; borders and spacing should establish most hierarchy.
- BASE: strong typography scale with fewer arbitrary font sizes.
- BASE: consistent spacing tokens and optical alignment.
- BASE: one primary action per local context; secondary actions remain visibly subordinate.
- BASE: iconography used where it improves recognition, not as decoration.
- BASE: muted color for structure; saturated color reserved for status and action.
- BASE: semantic status colors have icon/text redundancy and accessible contrast.
- BASE: motion communicates state transition; no ambient motion added merely for “polish.”
- BASE: skeletons only where layout is predictable; otherwise clear progress indicators.
- BASE: empty states tell the user the next useful action.
- BASE: error states explain whether data was preserved and what can be retried.
- BASE: “advanced” never means visually chaotic.

### Hero policy

- BASE: **compact hero is the default**, not a viewport-consuming marketing hero.
- BASE: organizer can choose `none`, `compact`, or `standard`.
- ADV: “immersive” / artwork-heavy hero is opt-in for events that deliberately want it.
- BASE: compact hero should usually fit event identity, date/status and one primary action in roughly 160–280 px on desktop.
- BASE: on project pages, project content should begin above or near the fold; avoid a decorative hero that pushes evidence down.
- BASE: on mobile, hero height should collapse aggressively.
- ADV: hero can be replaced with an event-specific lead block.
- ADV: image focal point/crop and responsive art direction.
- ADV: organizer preview at desktop/tablet/mobile.
- BASE: fallback identity should still look intentional when no artwork exists.

### Anti-slop rules

- Do not use gradients by default.
- Do not put icons in colored squares next to every heading.
- Do not use giant KPI cards when a compact summary strip or table is better.
- Do not use oversized marketing copy inside authenticated operator workflows.
- Do not overuse pills/badges for ordinary text.
- Do not make every section a card inside another card.
- Do not repeat the same label in heading, breadcrumb and card title.
- Do not hide frequently used actions behind three-dot menus merely to appear clean.
- Do not use a 3-column dashboard where the organizer needs a sortable data table.
- Do not make destructive operations red until the action itself; avoid a page covered in alarm colors.
- Do not add fake “AI” affordances to ordinary deterministic workflows.
- Do not display unhelpful decimals/precision just because the backend has them.
- Do not make advanced capabilities depend on memorizing opaque IDs.

## 5. Professional application-shell depth

- BASE: real route hierarchy with stable URLs, back/forward behavior and deep linking.
- BASE: event/workspace switcher with recent/favorite events.
- BASE: responsive persistent navigation that collapses to task-focused mobile navigation.
- BASE: breadcrumbs only where they add orientation.
- BASE: global command palette.
- BASE: global entity search.
- BASE: notification/inbox center.
- BASE: account/profile/preferences control.
- BASE: event state indicator (draft/open/judging/published/archived) always available but unobtrusive.
- ADV: recent objects and recent organizer actions.
- ADV: pinned organizer views.
- ADV: role switcher for users with multiple roles, with a clear “you are viewing as…” state.
- ADV: “preview as participant/judge/public” without unsafe impersonation.
- ADV: contextual side inspector that preserves list position.
- ADV: keyboard shortcut help overlay.
- ADV: configurable density: comfortable / compact / high-density.
- ADV: per-user table column preferences.
- ADV: workspace-aware tabs that preserve unsaved drafts.
- EXPERT: multi-pane operations mode for large desktop displays.
- EXPERT: command palette commands parameterized by selected entities.
- EXPERT: live operations mode with connection/realtime health state.
- PROG: route/view state is serializable enough to link to an exact operational context.

## 6. Universal data-grid and saved-view system

This is one of the highest-leverage UI primitives.

- BASE: sortable columns.
- BASE: search.
- BASE: structured filters.
- BASE: row selection.
- BASE: bulk-action bar.
- BASE: column show/hide.
- BASE: pagination or virtualized windowing depending on dataset.
- BASE: sticky header where appropriate.
- BASE: responsive fallback for narrow screens.
- ADV: nested AND/OR filter groups.
- ADV: filter operators appropriate to data type.
- ADV: saved private views.
- ADV: shared organizer views.
- ADV: favorite/pin views.
- ADV: URL-encoded shareable transient views.
- ADV: group/subgroup.
- ADV: list / board / matrix / calendar where semantically valid.
- ADV: aggregate footer values.
- ADV: computed columns.
- ADV: inline editing with validation.
- ADV: keyboard row navigation and range selection.
- ADV: split-pane inspection.
- ADV: “only changed since…” filter.
- ADV: view templates.
- EXPERT: text query language equivalent to UI filters.
- EXPERT: organization-managed canonical views.
- EXPERT: permission-aware columns/filters.
- EXPERT: export the current exact filtered view.
- EXPERT: subscribe to view changes.
- PROG: saved-view schema is accessible over API.
- PROG: CLI can run the same query.
- PROG: MCP can reference a saved view rather than re-send a giant filter.
- PROG: bulk operations can consume a saved view with a frozen membership snapshot.

---

# Part III — Massive subsystem feature atlas


## 7. Event creation, setup and lifecycle

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

## 8. Event templates, presets, cloning and reusable modules

Templates should evolve from “copy this event” into a reusable, versioned product primitive.
- BASE — Curated built-in templates with opinionated defaults.
- BASE — Preview a template before creating an event.
- BASE — Template explains which features it enables and why.
- ADV — Workspace template library.
- ADV — Versioned templates; existing events retain their pinned version.
- ADV — Upgrade preview from template v2 to v3.
- ADV — Template parameters: event name, dates, team size, judging duration, tracks.
- ADV — Optional template modules: mentor program, expo, sponsor challenges, community voting.
- ADV — Share/import/export templates.
- EXPERT — Composable modules with declared inputs, outputs and compatibility constraints.
- EXPERT — Organization baseline + event overlay.
- EXPERT — Template policy constraints: e.g. mandatory code-of-conduct acknowledgement.
- EXPERT — Template test suite run against synthetic event scenarios.
- EXPERT — Semantic migration hooks when a module version changes.
- PROG — Template/module registry used identically by UI and Event-as-Code.

## 9. Public event site

The public site should be a first-class website product, not an authenticated app with public routes.
- BASE — Compact identity header/hero with event name, dates, status and one action.
- BASE — Navigation for overview, schedule, challenges/tracks, projects, results, resources.
- BASE — excellent no-artwork default.
- BASE — SEO metadata, canonical URLs, OpenGraph cards and social images.
- BASE — fast anonymous rendering and cache-friendly data paths.
- BASE — accessible event status and deadline presentation.
- BASE — clear registration / submission / voting state based on current lifecycle.
- ADV — custom domain.
- ADV — event favicon and manifest.
- ADV — per-page metadata and social image.
- ADV — announcement banner with audience/schedule controls.
- ADV — multiple navigation layouts.
- ADV — page visibility windows.
- ADV — per-page access: public, registered, accepted, checked-in, team members.
- ADV — event-specific footer, legal links and sponsor placement.
- ADV — optional countdown block that does not dominate the page.
- ADV — content localization.
- ADV — static archive mode after event closes.
- EXPERT — edge/static pre-render of stable event pages.
- EXPERT — custom redirect map when organizers restructure pages.
- EXPERT — configurable CSP/embed policy by event.
- PROG — page structure exportable as configuration and independently versionable.

## 10. Theme, visual customization and design system

Customization should be deep enough that two Conflux events need not look like the same template, while keeping every customization inside accessibility and performance guardrails.
- BASE — curated default theme that needs zero organizer tuning.
- BASE — color palette with automatically derived accessible states.
- BASE — typography presets using safe, performant font stacks.
- BASE — compact/comfortable content density.
- BASE — logo, mark, banner and project-card artwork.
- BASE — hero: none/compact/standard; compact default.
- ADV — design token editor for colors, type scale, radius, spacing, borders and surfaces.
- ADV — light/dark/auto event theme modes.
- ADV — independent public-site and operator-workspace branding boundaries.
- ADV — multiple named theme presets in one event.
- ADV — responsive art direction and crop/focal point.
- ADV — layout width and grid presets.
- ADV — section-level background/surface variants.
- ADV — live WCAG contrast checks during editing.
- ADV — theme diff/history/rollback.
- ADV — export/import theme package.
- EXPERT — CSS-variable extension surface with allowlisted tokens, not arbitrary global CSS by default.
- EXPERT — custom font packages with licensing/size validation.
- EXPERT — event theme compatibility/conformance test across all block types.
- EXPERT — design-token inheritance from organization → event → page → block.
- PROG — theme schema is typed and available to extensions/Event-as-Code.
- PROG — extension blocks declare which theme tokens they consume.

## 11. Page builder and CMS

The existing schema-driven block model can become a Shopify-like compositional system without becoming a generic website builder.
- BASE — drag reorder sections.
- BASE — live preview.
- BASE — block presets with excellent defaults.
- BASE — undo/redo.
- BASE — autosave draft vs explicit publish.
- BASE — page-level publication status.
- ADV — nested blocks with bounded depth.
- ADV — reusable block/section instances.
- ADV — copy/paste blocks between pages/events.
- ADV — global reusable content snippets.
- ADV — conditional blocks by lifecycle/date/audience.
- ADV — block-level visibility rules.
- ADV — block version history and visual diff.
- ADV — multi-device preview.
- ADV — draft preview links.
- ADV — block presets grouped by purpose.
- ADV — dynamic data blocks driven by saved queries.
- ADV — per-block analytics impressions/clicks where privacy policy allows.
- ADV — localization variants.
- EXPERT — extension-contributed block types with declared schemas.
- EXPERT — block compatibility/version migrations.
- EXPERT — page templates and page-template inheritance.
- EXPERT — static safety analysis for broken links, missing media, inaccessible headings and excessive layout cost.
- PROG — canonical JSON/YAML page representation.
- PROG — schema-generated basic editor for any extension block.

## 12. Registration, applications, admissions and waitlists

A serious application subsystem can borrow from admissions/review systems while keeping the common “open registration” path trivial.
- BASE — open registration or approval-required registration.
- BASE — configurable registration window and capacity.
- BASE — draft application autosave.
- BASE — participant-facing status and next action.
- BASE — accepted/rejected/waitlisted/withdrawn/checked-in states.
- BASE — confirmation and RSVP workflow.
- ADV — multi-step application forms.
- ADV — conditional questions.
- ADV — reviewer queue with keyboard accept/reject/waitlist/undo.
- ADV — configurable reviewer rubric separate from project judging.
- ADV — blind application review.
- ADV — multiple admission reviewers with consensus/majority/manual decision policy.
- ADV — application comments and private reviewer notes.
- ADV — admission conflicts/recusal.
- ADV — waitlist rank/priority policies.
- ADV — automated waitlist promotion with capacity guardrails.
- ADV — per-cohort capacity targets and soft targets.
- ADV — application deduplication signals.
- ADV — document/file questions.
- ADV — participant correction/remediation request.
- EXPERT — staged admission workflow: screen → review → interview → decision.
- EXPERT — admissions calibration and inter-rater analysis.
- EXPERT — policy simulator for how a rule would affect current applicants.
- PROG — bulk admissions actions use dry-run and immutable decision receipts.

## 13. Identity, profiles, privacy and user history

Profiles should become reusable infrastructure across registration, matching, judging expertise, mentorship and portfolios.
- BASE — name, avatar, bio, links and skills.
- BASE — granular visibility for public/event-only/private profile fields.
- BASE — one person can have multiple roles in different events.
- BASE — profile completeness feedback only when a workflow needs it.
- ADV — education/employment/organization history.
- ADV — skill taxonomy with proficiency/evidence.
- ADV — availability and timezone.
- ADV — social/repository links with verification status.
- ADV — reusable application answers with explicit consent before reuse.
- ADV — cross-event participation history.
- ADV — cross-event judge/mentor history.
- ADV — configurable pronouns/display-name fields without requiring them.
- ADV — account export and data-deletion workflow.
- ADV — delegated organization identity linkage.
- EXPERT — verified organization/domain membership.
- EXPERT — relationship/conflict declarations reused by judging.
- EXPERT — provenance for imported profile data.
- EXPERT — privacy-preserving matching features that need not expose all profile fields.
- PROG — schema for custom profile attributes with retention/visibility policy.

## 14. Teams, invitations and matching

Team formation can be much deeper than a marketplace list.
- BASE — create/join/leave team within policy.
- BASE — invitation links and explicit invitations.
- BASE — team-size min/max validation.
- BASE — team readiness panel.
- BASE — teammate search by skills/interests.
- ADV — “looking for team” and “looking for members” structured profiles.
- ADV — desired skills vs offered skills.
- ADV — timezone/language/onsite-remote compatibility.
- ADV — project-interest tags.
- ADV — shortlist/bookmark candidates.
- ADV — match explanations based on organizer-visible deterministic features.
- ADV — recommendation tuning without exposing private scoring internals.
- ADV — team chat link/integration rather than forcing Conflux to become Slack.
- ADV — pre-event team matching sessions.
- ADV — organizer-assisted matching queue.
- ADV — team merge/split workflow with project/submission consequences previewed.
- EXPERT — optimization-based team formation with hard/soft constraints.
- EXPERT — diversity constraints only when explicitly configured and legally/ethically appropriate.
- EXPERT — stability analysis: who is unmatched and why.
- EXPERT — historical matching feedback to improve future matching rules.
- PROG — matching simulation endpoint and reproducible result seed.

## 15. Project authoring and technical story

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

## 16. Forms and custom data schemas

Forms already exist and are versioned. They can become a general schema system used across applications, submissions, judging and custom event workflows.
- BASE — text, textarea, number, date, select, multiselect, checkbox, URL, email and file fields.
- BASE — required/optional and clear validation messages.
- BASE — field descriptions and examples.
- ADV — conditional visibility based on prior answers.
- ADV — repeating groups.
- ADV — matrix/rating fields.
- ADV — structured person/team/project reference fields.
- ADV — Markdown/help text.
- ADV — field-level audience visibility.
- ADV — computed/read-only fields.
- ADV — reusable field libraries.
- ADV — section/page layout.
- ADV — draft schema vs published immutable schema versions.
- ADV — migration preview when changing schema after responses exist.
- ADV — export schema as JSON Schema-like representation.
- ADV — validation rules beyond simple type constraints.
- EXPERT — cross-field invariant expressions.
- EXPERT — custom extension field types.
- EXPERT — schema compatibility checker.
- EXPERT — schema test examples and fixtures.
- PROG — generated UI, API validation and Event-as-Code all consume the same schema.

## 17. Artifact upload, storage and evidence

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

## 18. Repository, demo, dataset and external-resource integration

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

## 19. Submission lifecycle, versioning and deadline correctness

Submission semantics are one of the places where “simple UI, rigorous backend” matters most.
- BASE — draft autosave.
- BASE — visible last-saved state.
- BASE — preflight before finalize.
- BASE — one clear finalization action.
- BASE — immutable finalized version.
- BASE — signed/hashed submission receipt.
- BASE — deadline shown in event timezone and local timezone.
- BASE — server is authoritative for deadline acceptance.
- ADV — reopen only under explicit policy/exception.
- ADV — multiple stage submissions with independent requirements.
- ADV — compare versions.
- ADV — explain why a version is judge-visible.
- ADV — finalization can freeze linked repository/artifact/content revisions.
- ADV — per-field finalization validation and direct links to fix.
- ADV — late/exception state explicit in evidence.
- ADV — idempotent finalize requests.
- ADV — queue/surge-safe finalization receipt even if downstream processing is deferred.
- EXPERT — cryptographic manifest of every judge-visible evidence element.
- EXPERT — deterministic reconstruction of a submission as-of deadline.
- EXPERT — dispute/review workflow for timestamp or evidence mismatch.
- PROG — submission state machine is introspectable, never inferred from scattered timestamps.

## 20. Submission CI, preflight, automated checks and provenance

The existing advanced submission CI concept can become a reusable verification engine rather than a handful of hardcoded checks.
- BASE — required field/link/artifact checks.
- BASE — repository accessible.
- BASE — demo URL resolves.
- BASE — license present when event requires it.
- BASE — deterministic pass/warn/fail categories.
- ADV — organizer-defined check pipeline.
- ADV — checks run on draft and finalization.
- ADV — async expensive checks with cached result by evidence digest.
- ADV — check explanations and remediation links.
- ADV — participant may re-run checks within rate limits.
- ADV — organizer waiver with reason and audit record.
- ADV — checks can emit structured facts consumed by eligibility rules.
- ADV — source tree constraints.
- ADV — dependency/license policy checks.
- ADV — security scanner integrations.
- ADV — artifact metadata validation.
- EXPERT — sandboxed build/test runner plugin.
- EXPERT — reproducible environment reference.
- EXPERT — provenance attestation for CI output.
- EXPERT — check version pinned to finalized evidence.
- EXPERT — historical re-evaluation clearly distinguished from original deadline result.
- PROG — checker SDK with strict input/output schema and resource limits.
- PROG — external check provider webhook with signed result.

## 21. Eligibility, policy and remediation

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

## 22. Rubric authoring and rubric laboratory

Rubrics should be treated as versioned evaluation instruments rather than a list of weighted sliders.
- BASE — weighted criteria with descriptions and scale anchors.
- BASE — score validation and autosave.
- BASE — published rubric version becomes immutable.
- ADV — criterion groups and nested sections.
- ADV — explicit scale descriptors for each score band.
- ADV — optional/non-applicable criterion policy.
- ADV — rubric preview with example project.
- ADV — rubric version diff.
- ADV — weight-sum and scoring-distribution diagnostics.
- ADV — test rubric against historical/synthetic ballots.
- ADV — simulate effect of weight changes on historical ranking.
- ADV — identify criteria with low variance or weak discrimination.
- ADV — judge feedback on confusing criteria.
- ADV — calibration examples with reference reasoning.
- EXPERT — inter-criterion correlation diagnostics.
- EXPERT — sensitivity to normalization choices.
- EXPERT — rubric fairness/stability analysis without pretending statistics prove normative fairness.
- EXPERT — multiple rubric variants by track/stage with shared inherited criteria.
- PROG — rubric is portable/versioned configuration usable by replay.

## 23. Judge directory, expertise, bidding and conflicts of interest

OpenReview-level assignment sophistication is a useful ceiling for Conflux's judging system.
- BASE — judge profile, capacity and availability.
- BASE — explicit conflicts/recusal.
- BASE — organizer-visible assignment progress.
- ADV — expertise taxonomy and proficiency.
- ADV — track preferences.
- ADV — project/topic bids: strong interest → no preference → avoid.
- ADV — max/min assignment preferences.
- ADV — availability windows for in-person judging.
- ADV — language constraints.
- ADV — declared organization/employment/mentor relationships.
- ADV — conflict policy with reason categories and visibility controls.
- ADV — organizer can add administrative conflict with reason.
- ADV — imported historical judge performance/load data.
- ADV — bulk judge import/update.
- ADV — reusable cross-event judge directory.
- EXPERT — computed affinity score from tags/text embeddings as an optional advisory signal.
- EXPERT — affinity explanation and manual override.
- EXPERT — conflict detection from declared relationships/history where data is available and consented.
- EXPERT — conflict policy year windows / relationship classes.
- EXPERT — judge reliability/calibration history used carefully as an assignment feature.
- PROG — judge constraints are structured inputs to assignment solver and replay.

## 24. Judge assignment optimization

Assignment is already a technical strength. It can become an operator-grade optimization laboratory.
- BASE — satisfy conflicts, capacity and required coverage.
- BASE — deterministic output for same inputs/seed.
- BASE — clear infeasibility errors.
- ADV — expertise affinity objective.
- ADV — bid preference objective.
- ADV — balanced workload.
- ADV — cross-judge overlap/connectivity objective for normalization.
- ADV — track/language/time-window constraints.
- ADV — locked/manual assignments respected.
- ADV — multiple candidate assignment plans.
- ADV — plan quality metrics.
- ADV — before/apply diff.
- ADV — organizer modifications followed by re-optimization of remainder.
- ADV — alternate/backup judge list.
- ADV — judge dropout simulation.
- ADV — project-demand overrides.
- EXPERT — configurable lexicographic hard/soft objectives.
- EXPERT — min-max, fair-flow and alternative solver strategies where useful.
- EXPERT — Pareto-style comparison of competing assignment objectives.
- EXPERT — solver reproducibility capsule with inputs/version/seed.
- EXPERT — stability analysis: how much does solution change if one judge drops?
- EXPERT — assignment recommendation explanation per judge/project.
- PROG — `plan`, `apply`, `revert-to-plan`, and saved assignment snapshots.

## 25. Scoring, calibration, normalization and reliability

This area can remain statistically sophisticated while being unusually transparent to organizers.
- BASE — raw rubric totals.
- BASE — normalized scores where configured.
- BASE — organizer explanation of normalization method.
- ADV — calibration round before live judging.
- ADV — reference projects/ballots.
- ADV — per-judge mean/variance and score-distribution diagnostics.
- ADV — inter-rater agreement metrics with appropriate caveats.
- ADV — criterion-level disagreement.
- ADV — outlier review queue.
- ADV — missing-score and partial-ballot policy.
- ADV — confidence field separate from score.
- ADV — compare raw vs normalized ranking.
- ADV — sensitivity to inclusion/exclusion of individual ballot.
- EXPERT — alternate defensible normalization models in a laboratory, never silently changed.
- EXPERT — judge-bias/model residual diagnostics.
- EXPERT — uncertainty intervals / bootstrap stability where assumptions support them.
- EXPERT — calibration drift over time.
- EXPERT — explicit model-version pinning and deterministic replay.
- PROG — every derived result carries source ballot/rubric/method versions.

## 26. Pairwise judging and ranking

Pairwise judging can become much more than a Bradley–Terry checkbox.
- BASE — fast A-vs-B decision UI.
- BASE — skip/recuse/tie policy.
- BASE — ranking generated from pairwise outcomes.
- ADV — adaptive pair selection maximizing information gain.
- ADV — avoid repeated same-judge/team interactions where possible.
- ADV — combine rubric and pairwise evidence.
- ADV — pairwise workload budget.
- ADV — ranking convergence/stability indicator.
- ADV — disconnected comparison graph diagnostics.
- ADV — suggest next comparisons to repair graph weakness.
- ADV — pairwise result sensitivity explorer.
- EXPERT — multiple ranking models available only through explicit configured method/version.
- EXPERT — uncertainty/stability analysis.
- EXPERT — active scheduling with judge expertise/COI constraints.
- EXPERT — audit graph showing which comparisons support a rank difference.
- PROG — deterministic schedule generation and replay.

## 27. Judge workspace UX

The judge surface should optimize for speed, focus, evidence quality and mistake prevention.
- BASE — queue left, project/evidence center, rubric right on wide screens.
- BASE — focused single-column mode on smaller screens.
- BASE — autosave with obvious saved/offline/error state.
- BASE — keyboard next/previous and scoring shortcuts.
- BASE — assignment progress.
- BASE — conflict/recusal always accessible.
- BASE — exact frozen submission evidence.
- ADV — resize/collapse panes.
- ADV — artifact tabs with preserved position.
- ADV — personal notes with explicit visibility.
- ADV — compare against rubric anchors.
- ADV — flag project for organizer review without changing score.
- ADV — offline draft buffer with deterministic reconciliation.
- ADV — route/schedule integration for physical events.
- ADV — time budget/pacing indicator.
- ADV — accessibility preference including high-contrast and text sizing.
- EXPERT — dual-project compare mode for pairwise.
- EXPERT — configurable judge workspace layout by evaluation method.
- EXPERT — local keyboard macro profile for high-volume judging.

## 28. Multi-round review, rebuttal, meta-review and appeals

Technical competitions can support conference-like workflows without forcing them on normal hackathons.
- BASE — multiple judging rounds/presets.
- ADV — different rubric and reviewer pool per round.
- ADV — soft deadline vs hard lock for judges.
- ADV — finalist advancement from round results.
- ADV — participant feedback release window.
- ADV — participant rebuttal/clarification window.
- ADV — judge response to rebuttal.
- ADV — meta-review / panel chair role.
- ADV — decision summary separate from raw reviews.
- ADV — appeal request with defined grounds and window.
- ADV — appeal reviewer isolated from original reviewer where configured.
- ADV — corrected decision version with audit trail.
- EXPERT — arbitrary review-stage template: review → rebuttal → meta-review → decision.
- EXPERT — stage-specific visibility matrix.
- EXPERT — ethics/safety review stage for events that need it.
- PROG — review-stage schema lives in the same stage graph rather than a second workflow engine.

## 29. Deliberation and winner finalization

The final decision room should be one of Conflux's strongest differentiators.
- BASE — finalist table with scores, rank, coverage and warnings.
- BASE — side-by-side finalist comparison.
- BASE — award eligibility shown inline.
- BASE — immutable finalization receipt.
- ADV — criterion-by-criterion comparison.
- ADV — disagreement and close-call indicators.
- ADV — pairwise/rubric evidence tabs.
- ADV — deliberation notes with author/time.
- ADV — panel stances separate from ballots.
- ADV — recusal from deliberation.
- ADV — explicit override reason when final choice differs from configured ranking.
- ADV — decision approval threshold / required approvers.
- ADV — no-self-approval option.
- ADV — conflict solver across overlapping awards.
- ADV — preview public result before publish.
- EXPERT — deterministic “why A ranks over B” evidence graph.
- EXPERT — sensitivity report for finalists.
- EXPERT — freeze all decision inputs into portable audit capsule.
- PROG — finalization operation is plan/approve/apply, not an opaque write.

## 30. Awards, prizes and fulfillment

Awards should model both selection logic and real fulfillment.
- BASE — cash/credit/physical/other typed prize.
- BASE — track/sponsor/global awards.
- BASE — winner count and eligibility.
- BASE — publication controls.
- ADV — composite award criteria.
- ADV — sponsor-specific judge pools.
- ADV — no-double-win / max-awards-per-project policies.
- ADV — award precedence and conflict resolution.
- ADV — honorable mentions.
- ADV — team-member-level entitlement splitting.
- ADV — fulfillment status: pending/contacted/verified/sent/claimed/expired.
- ADV — winner contact workflow.
- ADV — sponsor fulfillment export.
- ADV — tax/form/document checklist as configurable metadata, not legal advice.
- ADV — claim deadline and fallback winner workflow.
- EXPERT — optimization solver for award allocation under constraints.
- EXPERT — what-if allocation preview.
- EXPERT — signed award decision/fulfillment receipts.
- PROG — award configuration and allocation evidence export cleanly.

## 31. Community voting and abuse resistance

Community voting should remain optional but can become substantially more robust.
- BASE — clearly separate community vote from judge score.
- BASE — event-defined voting window.
- BASE — one-person/project constraints as configured.
- BASE — moderated project visibility.
- ADV — ranked voting / limited vote budget / favorites.
- ADV — category-specific voting.
- ADV — vote receipt visible to voter.
- ADV — anti-automation throttles.
- ADV — suspicious-pattern queue.
- ADV — transparent invalidation reason.
- ADV — re-run results after invalidated votes with audit.
- ADV — geographic/IP/device signals treated only as risk signals, not identity truth.
- ADV — organizer-set eligibility to vote: registered, accepted, checked-in, public.
- EXPERT — anomaly analytics with explainable features.
- EXPERT — privacy-preserving aggregate risk metrics.
- EXPERT — deterministic fraud-review case bundles.
- PROG — voting method/version embedded in result publication evidence.

## 32. Sponsor challenge and developer-resource center

Sponsors can get a real subsystem instead of static logos plus prize text.
- BASE — sponsor profile and challenge description.
- BASE — prize/eligibility link.
- BASE — resources, docs, starter repositories and support contacts.
- BASE — FAQ.
- ADV — challenge-specific submission requirements.
- ADV — sponsor judge pool.
- ADV — workshop/session linkage.
- ADV — API key/credit claim instructions with access control.
- ADV — resource version/update notices.
- ADV — sponsor announcements scoped to challenge participants.
- ADV — challenge opt-in/bookmark.
- ADV — sponsor office hours.
- ADV — challenge analytics: views, opt-ins, eligible projects.
- ADV — sponsor portal with least-privilege permissions.
- ADV — sponsor feedback after judging.
- EXPERT — sandbox credential issuance via extension/integration providers.
- EXPERT — sponsor API usage evidence only where participants opt into collection.
- PROG — sponsor resource types are extension-friendly and archiveable.

## 33. Mentorship, support requests and office hours

Mentorship can become an operations queue optimized for getting teams unstuck.
- BASE — request help with topic/urgency.
- BASE — mentor expertise and availability.
- BASE — claim/reassign/resolve.
- BASE — participant-visible status.
- BASE — office-hours slots.
- ADV — triage categories.
- ADV — estimated wait time from queue state, clearly approximate.
- ADV — match by expertise/location/language.
- ADV — team can close/cancel request.
- ADV — mentor private note vs participant-visible resolution note.
- ADV — request history by team.
- ADV — organizer SLA/queue dashboard.
- ADV — on-site room/table assignment.
- ADV — calendar integration.
- ADV — follow-up rating.
- EXPERT — dispatch optimization under load.
- EXPERT — repeat-problem analytics that feed event FAQ/announcements.
- PROG — integrations can create/resolve requests from Discord/Slack without creating a competing chat product.

## 34. Communications, inbox, notifications and automation

Communications should be event-aware and audience-aware, not a generic mail blast form.
- BASE — announcements.
- BASE — targeted email/in-app delivery.
- BASE — participant inbox.
- BASE — scheduled send.
- BASE — delivery status.
- ADV — dynamic audience from saved query/view.
- ADV — preview exact recipient count before send.
- ADV — sample recipient preview.
- ADV — templates with structured variables.
- ADV — localization variants.
- ADV — quiet hours/timezone-aware delivery.
- ADV — digest mode.
- ADV — organizer approval before mass send.
- ADV — retry/bounce status from email provider.
- ADV — Discord/Slack webhook/channel delivery adapters.
- ADV — event-triggered automation: acceptance, deadline, check-in, result publication.
- ADV — unsubscribe/preference categories where legally appropriate.
- EXPERT — message sequence/campaign with stop conditions.
- EXPERT — communications audit including rendered template version.
- PROG — audience query + message template + schedule are configuration objects.

## 35. Hybrid/in-person check-in and access control

pretix demonstrates how deep “check-in” can become. Conflux can take the relevant event-operations parts without turning into a ticketing platform.
- BASE — QR and manual lookup check-in.
- BASE — volunteer-scoped check-in permissions.
- BASE — check-in timestamp and operator/device.
- BASE — duplicate scan explanation.
- ADV — multiple independent check-in lists: event entrance, workshop, judging expo, meal, restricted room.
- ADV — list eligibility by role/track/status.
- ADV — check-out / re-entry.
- ADV — multiple-entry policy.
- ADV — gate/device identifiers.
- ADV — failed-scan logs with reason.
- ADV — participant badge lookup.
- ADV — badge printing on check-in.
- ADV — badge layout templates.
- ADV — attendance certificate trigger.
- ADV — offline scanner queue with nonce/idempotency and sync reconciliation.
- ADV — explicit stale-data warning in offline mode.
- EXPERT — access policy simulator.
- EXPERT — device enrollment/revocation.
- EXPERT — venue-wide live attendance occupancy by zone where configured.
- PROG — scanner API designed for untrusted scanned input and least privilege.

## 36. Floorplans, booths, rooms and spatial logistics

On-site logistics are already present; depth can turn them into a genuine operations system.
- BASE — assign project to table/booth/room.
- BASE — printable fallback layout.
- BASE — judge route over assigned projects.
- ADV — visual floorplan editor.
- ADV — zones and room capacities.
- ADV — accessibility constraints.
- ADV — power/network/special-equipment attributes.
- ADV — sponsor/track grouping preferences.
- ADV — adjacency constraints/preferences.
- ADV — automatic placement with hard/soft constraints.
- ADV — move/drag placement with immediate conflict diagnostics.
- ADV — QR table signage.
- ADV — participant-facing booth location.
- ADV — judge mobile route with completed/next stops.
- ADV — live reassignment after no-show.
- EXPERT — walking-time matrix / route optimization.
- EXPERT — infeasibility diagnosis explaining which constraints conflict.
- EXPERT — congestion-aware routing as an optional advanced model.
- PROG — floorplan/layout export to portable geometry JSON and print renderer.

## 37. Schedule, sessions, workshops and livestreams

A hackathon schedule should be more than static text.
- BASE — sessions with time/location/title/speaker.
- BASE — timezone-aware public schedule.
- BASE — calendar export.
- ADV — tracks/rooms.
- ADV — RSVP/capacity.
- ADV — waiting list for limited session.
- ADV — livestream/recording link.
- ADV — session resources/slides.
- ADV — speaker profiles.
- ADV — participant personal schedule.
- ADV — reminders.
- ADV — cancellation/location-change push.
- ADV — session check-in.
- ADV — mentor/sponsor workshop linkage.
- EXPERT — schedule conflict detector.
- EXPERT — room capacity and equipment constraints.
- EXPERT — automatic schedule proposal from constraints.
- PROG — iCalendar/API/webhook representation.

## 38. Public gallery, search and project discovery

The gallery can become an excellent technical-project discovery surface rather than a card grid.
- BASE — fast search.
- BASE — track/tag filters.
- BASE — sort options with explicit semantics.
- BASE — strong project cards.
- BASE — accessible project detail pages.
- ADV — full-text search over project story and metadata.
- ADV — filter by technologies/custom taxonomy/award/status.
- ADV — saved/shareable public searches.
- ADV — featured collections curated by organizer.
- ADV — random/discovery mode that does not bias official ranking.
- ADV — related projects by explicit tags; ML similarity optional.
- ADV — compare projects.
- ADV — filter to projects with demo/repo/paper/dataset.
- ADV — static archive search after event.
- EXPERT — public search syntax for power users.
- EXPERT — federated search across events in a workspace/org.
- PROG — public search API respects publication/retention policy.

## 39. Results, publication and storytelling

Publication should turn complex judging evidence into a clean, credible public outcome.
- BASE — winners by award/track.
- BASE — project cards and links.
- BASE — publication preview.
- BASE — scheduled publication.
- ADV — finalist pages.
- ADV — organizer-written result narrative.
- ADV — shareable winner cards.
- ADV — result correction notices with visible history.
- ADV — feedback release independently scheduled from winners.
- ADV — per-award explanation policy.
- ADV — public judge list where event chooses to publish it.
- ADV — photo/media gallery.
- ADV — statistics/participation recap.
- ADV — sponsor acknowledgment.
- ADV — permanent static archive.
- EXPERT — signed results manifest.
- EXPERT — machine-readable result feed.
- PROG — publication is atomic across web/API/archive rather than a series of toggles.

## 40. Portfolio and post-event continuation

Post-event continuation can turn Conflux into durable project infrastructure without becoming a social network.
- BASE — participant portfolio of published projects.
- BASE — awards and event participation.
- BASE — opt-in public visibility.
- BASE — project page persists after event.
- ADV — post-event project updates clearly separated from judged snapshot.
- ADV — changelog/milestones.
- ADV — updated demo/repo links.
- ADV — continuation collaborators.
- ADV — organizer can archive/hide abusive or broken continuations.
- ADV — export portfolio data.
- ADV — static portfolio card/embed.
- EXPERT — project lineage across multiple events/iterations.
- EXPERT — attach publications/releases after event.
- EXPERT — immutable “as judged” tab alongside living project.
- PROG — portable project archive enables migration away from Conflux.

## 41. Search, query language and saved views

A universal query engine can unify organizer tables, analytics, exports, communications audiences, bulk ops, CLI and MCP.
- BASE — simple search box on every major collection.
- BASE — visual filter builder.
- ADV — nested boolean conditions.
- ADV — typed operators by field.
- ADV — relative time operators.
- ADV — relation filters: team has member, project has finding, judge has conflict.
- ADV — aggregate predicates where safe: review count < 2.
- ADV — named saved views.
- ADV — share/favorite/pin.
- ADV — dynamic columns.
- ADV — query diagnostics when a filter is expensive.
- EXPERT — text query syntax with autocomplete.
- EXPERT — formulas/computed fields.
- EXPERT — permission-safe cross-domain queries.
- EXPERT — query plan/cost guardrails.
- PROG — same query AST used by UI/API/CLI/MCP.
- PROG — saved query can drive communication audience, export, dashboard widget or bulk operation.

## 42. Bulk organizer operations

Bulk actions should be powerful precisely because they are safe and reviewable.
- BASE — select visible/filtered rows.
- BASE — clear recipient/object count.
- BASE — common safe bulk edits.
- ADV — operate on frozen saved-view membership.
- ADV — dry-run with per-object outcome.
- ADV — validation failures grouped before apply.
- ADV — conflict detection if objects change after preview.
- ADV — exact execution receipt.
- ADV — async execution for large sets.
- ADV — progress and cancellation where safe.
- ADV — retry failed subset.
- ADV — compensating rollback for reversible actions.
- ADV — approval requirement based on action/risk/size.
- EXPERT — import CSV assignment/action plan then dry-run atomically, similar to mature conference systems.
- EXPERT — operation templates.
- PROG — bulk planner is a general backend primitive reused by CLI/MCP.

## 43. Analytics and operational intelligence

Analytics should answer operational questions, not merely display decorative charts.
- BASE — registration/application/team/project/submission funnel.
- BASE — judging completion and workload.
- BASE — check-in counts.
- BASE — mentor queue state.
- BASE — award/publication readiness.
- ADV — segment by track/cohort/status/custom taxonomy.
- ADV — time-series for submissions/finalizations near deadline.
- ADV — filterable distributions for judge scoring.
- ADV — query-to-chart from saved views.
- ADV — export underlying rows.
- ADV — data freshness timestamp.
- ADV — event health panel with actionable threshold alerts.
- ADV — compare current event against its own prior stage or prior edition.
- ADV — custom dashboard layout.
- EXPERT — anomaly detection only where explainable and actionable.
- EXPERT — capacity forecasting using observed workload.
- EXPERT — privacy-aware aggregate suppression for small groups.
- PROG — analytics metrics have documented definitions and versioning.

## 44. Governance, approvals, receipts and exceptions

Governance is a cross-cutting differentiator: high-impact operations can be explainable and reviewable without making every action bureaucratic.
- BASE — event rules publication and acknowledgement.
- BASE — deadline exception request/grant.
- BASE — audited publication.
- ADV — generic approval policy: one approver / N-of-M / role requirement.
- ADV — no-self-approval.
- ADV — approval expiration.
- ADV — scheduled approved operation.
- ADV — change request/comments on pending operation.
- ADV — high-impact operation risk classification.
- ADV — signed/hashed receipts for submission, judging finalization and publication.
- ADV — correction workflow preserving prior public result.
- ADV — governance dashboard of pending approvals/exceptions.
- EXPERT — configurable policy requiring approval above blast-radius threshold.
- EXPERT — portable evidence package for external audit.
- PROG — operation-plan object can be consumed by UI, CLI and MCP consistently.

## 45. Audit and provenance explorer

The audit log can become a first-class debugging and trust surface.
- BASE — readable actor/action/object/time entries.
- BASE — filter by actor/object/action.
- BASE — link to affected object.
- ADV — before/after semantic diff for configuration changes.
- ADV — correlation ID across API → task → webhook.
- ADV — grouped transaction view.
- ADV — provenance chain from submission → checks → ballots → normalized result → award → publication.
- ADV — human-readable explanation for system-generated action.
- ADV — export filtered audit slice.
- ADV — retention controls.
- ADV — integrity verification status.
- EXPERT — replay link when action is reproducible.
- EXPERT — signed audit capsule for a decision.
- EXPERT — trace visualization across asynchronous workers/integrations.
- PROG — audit event schemas are versioned and extension events use registered namespaces.

## 46. Event-as-Code: next depth after current plan/apply implementation

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

## 47. REST API, OpenAPI and generated SDK depth

The API is already a real product surface. It should become difficult for the UI and automation layers to drift away from it.
- BASE/PROG — consistent pagination/error/idempotency conventions.
- PROG — generated TypeScript/Python SDKs remain contract-tested.
- PROG — operation IDs designed as stable developer-facing names.
- PROG — full schema examples.
- PROG — conditional request/ETag support on high-contention configuration where useful.
- PROG — idempotency keys for mutation classes vulnerable to retries.
- PROG — consistent async-job response shape.
- PROG — batch read endpoints where latency meaningfully improves.
- PROG — bulk operations through explicit plan/apply endpoints.
- PROG — versioned webhook event schemas.
- PROG — deprecation metadata and migration guide.
- PROG — compatibility tests against previous supported API version.
- PROG — API explorer generated from actual schema plus domain examples.
- EXPERT — sparse fieldsets / includes only if justified by large operator clients.
- EXPERT — cursor pagination for very large mutable collections where offset becomes problematic.
- EXPERT — conditional streaming/export endpoints for large datasets.

## 48. CLI: from wrapper to serious operator shell

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

## 49. MCP / agent-native operations

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

## 50. Extension SDK and plugin ecosystem

The extension SDK can make extreme customization sustainable, but only if it is declarative-first and capability-scoped.
- BASE — first-party install ships fully useful with no extensions.
- PROG — extension manifest with name/version/compatibility/capabilities.
- PROG — explicit extension points, not arbitrary imports into internal modules.
- PROG — artifact renderer extension.
- PROG — preflight/checker extension.
- PROG — import/export adapter extension.
- PROG — page block extension.
- PROG — form field extension.
- PROG — judging strategy/diagnostic extension.
- PROG — integration/provider extension.
- PROG — notification channel extension.
- PROG — analytics widget extension.
- PROG — custom Event-as-Code resource/config schema.
- PROG — schema-generated fallback UI for extension config.
- PROG — optional custom React UI under a restricted stable component/API surface.
- ADV — per-event enable/disable.
- ADV — extension settings versioning and migration.
- ADV — extension permission/capability declaration.
- ADV — extension health/status surface.
- EXPERT — sandbox or process isolation for untrusted executable extensions where feasible.
- EXPERT — declarative extension class that executes no arbitrary code.
- EXPERT — trusted/restricted mode for installations/extensions.
- EXPERT — signed packages/checksums.
- EXPERT — extension conformance test kit.
- EXPERT — compatibility matrix against Conflux releases.
- EXPERT — reference extension for each supported family.
- EXPERT — extension marketplace/catalog can be optional and decentralized.

## 51. Webhooks and integrations

The current signed/retrying webhook foundation can become an integration control plane.
- BASE — event types and delivery history.
- BASE — signing secret rotation.
- BASE — retry/backoff.
- BASE — manual replay.
- ADV — endpoint-level event filters.
- ADV — payload version pinning.
- ADV — test delivery with synthetic event.
- ADV — secret masking.
- ADV — disabled-after-repeated-failure policy.
- ADV — replay selected historical delivery.
- ADV — compare original/replayed payload.
- ADV — per-endpoint rate limits.
- ADV — dead-letter view.
- ADV — integration health dashboard.
- EXPERT — transform/filter step using constrained declarative mapping.
- EXPERT — inbound webhook adapters with signature verification.
- EXPERT — exactly-once impossible caveat handled via stable event IDs/idempotency.
- PROG — extension SDK can register integration type and UI config schema.

## 52. Import, export, migration and no-lock-in

No-lock-in should be a product promise backed by concrete migration tooling.
- BASE — canonical configuration export.
- BASE — full event archive export.
- BASE — CSV exports for ordinary entities.
- ADV — migration preview before import.
- ADV — field mapping UI.
- ADV — unsupported-data report.
- ADV — deterministic identity rewriting.
- ADV — media/artifact migration manifest.
- ADV — import dry-run.
- ADV — resumable large migration.
- ADV — adapter for common hackathon exports where formats are available.
- ADV — preserve source-system identifiers as provenance metadata.
- ADV — static public archive export.
- EXPERT — signed portable archive.
- EXPERT — round-trip compatibility tests.
- EXPERT — migration adapter SDK.
- EXPERT — archive schema version migration.
- PROG — migration is observable as async job with per-record failures and retry.

## 53. Permissions, authorization and delegated roles

The role model can grow without becoming an enterprise IAM project by adding composable scopes and policy diagnostics.
- BASE — participant/judge/mentor/volunteer/organizer/admin roles.
- BASE — event/workspace scope obvious in UI.
- ADV — custom limited organizer roles.
- ADV — permission bundles.
- ADV — track/stage-specific permissions.
- ADV — sponsor-scoped access.
- ADV — read vs decide vs publish separation.
- ADV — temporary role grant with expiration.
- ADV — service/API credentials bound to actor and scope.
- ADV — permission explanation: “why can/can't this user do X?”
- ADV — preview permissions as role without impersonating credentials.
- ADV — bulk role assignment with dry-run.
- EXPERT — attribute/policy rules only where role bundles are insufficient.
- EXPERT — break-glass operation with explicit audit.
- PROG — extension capabilities must map into the same authorization framework.

## 54. Security and adversarial hardening

Advanced customization raises the security bar; rich content, extensions, imports and agents need explicit trust boundaries.
- BASE — CSRF/session hardening.
- BASE — object-level authorization tests.
- BASE — secure artifact serving.
- BASE — rate limits on abuse-prone endpoints.
- ADV — content security policy.
- ADV — Trusted Types evaluation for frontend unsafe sinks.
- ADV — sanitizer centralization and version tracking.
- ADV — file/archive path traversal protections.
- ADV — image/PDF parser isolation strategy.
- ADV — SSRF controls for URL previews/checkers.
- ADV — webhook destination validation.
- ADV — secret rotation workflows.
- ADV — dependency and container scanning.
- ADV — audit alert on high-impact credential usage.
- EXPERT — fuzz Event-as-Code/import/rich-text schemas.
- EXPERT — property tests for state-machine invariants.
- EXPERT — authorization matrix generated from routes/actions and tested.
- EXPERT — extension threat model/capability sandbox.
- EXPERT — agent prompt-injection threat model and tainted-content handling.
- PROG — security-sensitive operations expose reasoned failure, never hidden bypass flags.

## 55. Performance, deadline surge and scalability

The goal should be predictable behavior at deadline cliffs, not vanity aggregate RPS.
- BASE — publish workload-specific p50/p95/p99 for core flows.
- BASE — no integrity regression under load.
- ADV — scenarios for gallery browse, draft autosave, uploads, finalize, judging, voting, organizer dashboards and webhooks.
- ADV — connection-pool instrumentation.
- ADV — slow-query reporting.
- ADV — N+1 regression tests for high-volume endpoints.
- ADV — background expensive exports/reports.
- ADV — backpressure for organizer-heavy actions.
- ADV — cache only measured read hotspots.
- ADV — deadline finalization fast path that records durable intent/receipt before optional expensive follow-up.
- ADV — object-storage multipart/resume where large artifacts justify it.
- ADV — public static/cache strategy after publication.
- ADV — async fanout for messages/webhooks.
- EXPERT — synthetic event generator at 1k/10k/50k participants.
- EXPERT — chaos under load: worker restart, DB latency, object-store delay.
- EXPERT — capacity model based on event size and enabled features.
- EXPERT — automatic warning when configured deployment is below measured capacity envelope.
- PROG — performance evidence generated as versioned reports, not anecdotal claims.

## 56. Offline/PWA and degraded-network behavior

Offline should target on-site workflows where it creates real value.
- BASE — app clearly distinguishes offline vs online.
- ADV — judge draft scores can buffer locally and reconcile safely.
- ADV — check-in scanner offline data bundle.
- ADV — offline scan nonce/idempotency.
- ADV — participant QR pass available offline.
- ADV — cached schedule/resources.
- ADV — organizer emergency contact/list snapshot.
- ADV — conflict UX when server changed during offline edit.
- ADV — background sync state.
- ADV — explicit stale-data timestamp.
- EXPERT — selective offline event package by role/device.
- EXPERT — encryption at rest for sensitive offline device data.
- EXPERT — remote device/session revocation once online.
- PROG — offline-capable operations declare reconciliation semantics.

## 57. Accessibility as a product system

Conflux already has accessibility work; the target can be continuous conformance rather than one audit.
- BASE — keyboard navigation.
- BASE — visible focus.
- BASE — semantic headings/landmarks.
- BASE — contrast-compliant default theme.
- BASE — form errors tied to fields.
- BASE — status never color-only.
- ADV — theme editor blocks inaccessible combinations.
- ADV — project story lints missing alt text/heading skips.
- ADV — table/grid screen-reader strategy.
- ADV — reduced-motion support.
- ADV — text scaling without loss of function.
- ADV — math accessibility output.
- ADV — PDF/badge accessibility guidance where technically possible.
- ADV — organizer accessibility conformance report.
- ADV — automated axe-like checks plus documented manual checks.
- EXPERT — extension block conformance contract.
- EXPERT — accessibility snapshot regression suite across themes.
- PROG — accessibility findings have stable machine-readable codes.

## 58. Internationalization, locales, calendars and timezones

Events are deadline-heavy; timezone behavior must be deeper than translated strings.
- BASE — every deadline stores an unambiguous instant + event timezone context.
- BASE — user sees event timezone and optionally local timezone.
- BASE — DST ambiguity/nonexistent-time warnings in organizer editor.
- ADV — localized UI strings.
- ADV — localized public pages.
- ADV — localized rich-content variants.
- ADV — locale-aware number/date formatting.
- ADV — right-to-left layout support.
- ADV — language preference in profile.
- ADV — message template locale fallback.
- ADV — translated form labels/help while response schema stays stable.
- EXPERT — locale completeness report for an event.
- EXPERT — custom terminology/taxonomy labels by locale.
- PROG — APIs return stable codes, not localized strings as identifiers.

## 59. Organizations, multi-event and enterprise layer

This is useful, but relative to the existing architecture it is not the hardest or most differentiating work. Keep it thin and leverage the event primitives.
- BASE — organization containing workspaces/events.
- BASE — org membership and role.
- BASE — event portfolio.
- ADV — reusable org themes/templates.
- ADV — reusable judge/mentor directory.
- ADV — organization integration credentials.
- ADV — custom domain management.
- ADV — cross-event reporting.
- ADV — organization retention policy defaults.
- ADV — organization approval policies.
- ADV — organization audit aggregation.
- ADV — organization-wide custom taxonomy.
- EXPERT — multiple identity providers.
- EXPERT — SAML/SCIM only when real demand justifies it.
- EXPERT — delegated event administration.
- EXPERT — policy packs enforced across events.
- PROG — org defaults layer cleanly beneath event overrides.

## 60. Self-hosting, deployment and observability

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

## 61. Testing, fixtures, scenario generation and verification velocity

Given the hackathon experience, the verification architecture itself is a product-development multiplier.
- BASE — backend fast tests stay fast; profile slowest tail rather than over-optimize everything.
- BASE — persistent dev stack with HMR.
- BASE — deterministic fixtures.
- BASE — isolated E2E event/workspace per test or shard where mutation occurs.
- BASE — reusable auth storage state.
- BASE — browser traces/screenshots/video on failure by default.
- ADV — affected-test selection.
- ADV — smoke / PR / full / release browser tiers.
- ADV — scenario generator for event sizes and enabled feature combinations.
- ADV — fixtures for each lifecycle state.
- ADV — time-control helpers for deadline testing.
- ADV — concurrency harness for finalize/vote/score/publish races.
- ADV — visual regression for stable critical surfaces.
- ADV — accessibility regression.
- ADV — API/SDK schema drift gate.
- EXPERT — mutation/property testing for policy and workflow invariants.
- EXPERT — chaos suite.
- EXPERT — performance regression budget by endpoint/workload.
- EXPERT — extension conformance suite.
- PROG — every reference scenario can be generated via CLI for contributors and demos.

## 62. Optional automated-evaluation competition modes

Conflux can eventually support more than hackathons—ML challenges, programming contests, benchmarks, data competitions—without putting those concepts into the default hackathon UI.
- OPTIONAL — event template for automatic metric-based competition.
- OPTIONAL — hidden/public test split.
- OPTIONAL — submission attempt limits.
- OPTIONAL — queued evaluation jobs.
- OPTIONAL — leaderboard.
- OPTIONAL — frozen evaluation container/image/version.
- OPTIONAL — custom metric plugin.
- OPTIONAL — anti-leakage/public-private leaderboard policy.
- OPTIONAL — code submission from pinned repository/artifact.
- OPTIONAL — benchmark result artifact and logs.
- OPTIONAL — compute quota.
- OPTIONAL — manual judging + automated metric hybrid.
- EXPERT — sandbox isolation/resource limits.
- EXPERT — reproducibility bundle.
- EXPERT — evaluation rerun under new metric version is clearly distinguished from original official result.
- PROG — evaluator extension interface independent of core judging.

## 63. Organizer operations center

The operations center should become a high-density command surface for live events.
- BASE — readiness, deadlines, active incidents and queues in one screen.
- BASE — participant/application/submission/judging counts.
- BASE — direct link from metric to filtered underlying records.
- ADV — customizable widgets from saved views.
- ADV — live judging completion.
- ADV — check-in/mentor/eligibility queue status.
- ADV — webhook/email/task failures.
- ADV — recent high-impact audit events.
- ADV — event timeline with next scheduled transitions.
- ADV — alert acknowledgment/assignment.
- ADV — incident note log.
- ADV — operations layout saved per user.
- EXPERT — big-screen operations layout.
- EXPERT — threshold/rule-driven alerts with cooldown.
- PROG — dashboard widgets use same query/metric definitions as analytics API.

## 64. Event readiness, simulation and rehearsal

A highly advanced platform should help organizers prove that their configuration works before participants encounter it.
- BASE — pre-launch readiness checklist from actual configuration.
- BASE — test participant/judge accounts.
- ADV — synthetic participant/team/project generator.
- ADV — simulate application → team → submission → eligibility → judging → awards → publish.
- ADV — run deadline transitions in accelerated virtual time.
- ADV — show missing email/template/resource dependencies.
- ADV — detect impossible stage/policy combinations.
- ADV — detect judge capacity shortage before assignments.
- ADV — detect award eligibility impossible/undersubscribed.
- ADV — detect check-in/floorplan capacity issues.
- ADV — verify public-site links/media.
- ADV — dry-run communication audience.
- ADV — dry-run Event-as-Code plan against rehearsal copy.
- EXPERT — stochastic dropout/no-show simulation.
- EXPERT — deadline surge load scenario generated from current event size.
- EXPERT — “launch certification” evidence report.

## 65. Custom taxonomies, metadata and semantic organization

Custom taxonomies can become connective tissue across matching, search, analytics, permissions and content.
- BASE — organizer-defined project/person/event tags.
- ADV — hierarchical taxonomy.
- ADV — synonyms/aliases.
- ADV — controlled vocabulary vs free-form tag distinction.
- ADV — tag colors/icons only where helpful.
- ADV — per-object-type applicability.
- ADV — required/optional taxonomy fields.
- ADV — public/private/internal visibility.
- ADV — taxonomy migration/rename/merge.
- ADV — bulk retagging with preview.
- ADV — taxonomy-driven saved views and page collections.
- EXPERT — taxonomy values as assignment expertise/bid dimensions.
- EXPERT — taxonomy provenance when imported from external system.
- PROG — stable taxonomy IDs independent of display labels/localization.

## 66. Feedback and post-judging participant experience

Feedback release can become a thoughtful product, not a dump of judge comments.
- BASE — release judge feedback after configured time.
- BASE — organizer controls anonymous/named attribution.
- BASE — hide internal-only notes.
- ADV — criterion-level feedback.
- ADV — organizer redaction workflow preserving original internally.
- ADV — feedback quality checklist.
- ADV — participant acknowledge/read receipt.
- ADV — participant clarification question window.
- ADV — judge answer workflow.
- ADV — meta-review summary.
- ADV — downloadable feedback packet.
- EXPERT — review-quality rating by organizers or participants with guardrails.
- EXPERT — calibration analytics incorporate review-quality signals without silently changing official scores.
- PROG — feedback release uses immutable selected source versions.

## 67. Moderation and trust/safety queues

Community/public content requires a structured but proportionate moderation system.
- BASE — report project/comment/content.
- BASE — organizer moderation queue.
- BASE — hide/unhide with reason.
- ADV — category/severity.
- ADV — assignment to moderator.
- ADV — evidence snapshot at report time.
- ADV — participant appeal of moderation where event enables it.
- ADV — spam/rate signals.
- ADV — duplicate report grouping.
- ADV — action templates.
- ADV — public correction/reinstatement status when appropriate.
- EXPERT — extension hooks for external moderation scanners.
- EXPERT — audit separation between automated signal and human decision.
- PROG — moderation state is never conflated with judging/eligibility unless an explicit policy connects them.

## 68. Developer experience, docs and reference environments

If Conflux becomes extremely deep, documentation must become part of the architecture.
- BASE — quickstart that genuinely works.
- BASE — operator guide organized by lifecycle.
- BASE — participant/judge guides generated from enabled features where possible.
- ADV — API recipes.
- ADV — Event-as-Code examples.
- ADV — extension SDK reference examples.
- ADV — architecture decision records.
- ADV — compatibility/support matrix.
- ADV — interactive demo event.
- ADV — documented domain glossary.
- ADV — “how this feature composes with…” links.
- ADV — generated schema docs from source metadata.
- EXPERT — local docs search.
- EXPERT — runnable tutorial fixtures.
- EXPERT — upgrade cookbook with semantic config/API changes.
- PROG — examples validated in CI so docs do not rot.

## 69. Cross-event research and benchmarking exports

For organizers running recurring programs, careful research exports can be valuable without turning Conflux into an opaque analytics vendor.
- ADV — de-identified export profile.
- ADV — configurable field suppression.
- ADV — stable event/track/stage dimensions.
- ADV — judging diagnostics export.
- ADV — participation funnel export.
- ADV — schema/data dictionary bundled with export.
- ADV — provenance/version of derived metrics.
- EXPERT — longitudinal cross-event project/participant analysis only with appropriate consent/legal basis.
- EXPERT — differential/privacy-preserving techniques are possible future work, not a default claim.
- PROG — export is reproducible from saved query + metric version.

## 70. Architecture-wide feature interactions worth exploiting

The largest gains come from combining existing systems rather than adding isolated screens.
- Event-as-Code + page builder: public site/theme/layout can be reviewed in Git and previewed from a branch.
- Event-as-Code + governance: risky config plan requires approval and can be scheduled.
- Query engine + communications: message exactly the teams matching a saved operational condition.
- Query engine + bulk ops: dry-run remediation over the same frozen set.
- Query engine + analytics: chart and table are two views of one definition.
- Audit + judging replay: every official result can point to a reproducible computation capsule.
- Rich project document + submission versioning: judge sees exact renderer/content/media revision used at deadline.
- Rich project document + archive: permanent static technical project page remains faithful after renderer upgrades.
- Profiles + judging: expertise/conflicts/capacity reuse profile primitives.
- Profiles + mentorship: same skills model drives mentor matching.
- Taxonomy + judging: tags drive expertise/bids/award eligibility without hardcoding category columns.
- On-site floorplan + judge assignment: optimize both expertise coverage and walking distance.
- Check-in + communication: target urgent venue changes only to checked-in attendees when appropriate.
- Schedule + notifications: automatic location/time updates.
- Sponsor resources + mentorship: sponsor engineers expose dedicated office hours for challenge participants.
- Submission CI + eligibility: checks produce facts; policy determines eligibility; organizers can waive with audit.
- MCP + operation planner: agent can propose a mass change without obtaining direct raw mutation capability.
- MCP + resources/skills: agents discover event-specific procedures and authoritative data without dumping whole datasets.
- Extension SDK + schema UI: new extension config gets a safe generic editor before custom UI exists.
- Extension SDK + Event-as-Code: extension config remains portable and reviewable.
- Extension SDK + archives: plugin data needs declared portability/retention behavior.
- Offline task model + onsite: scanner/judge operations reconcile through the same idempotent operation primitives.
- Organization layer + templates: organization is mostly inheritance/reuse, not a duplicate event engine.

---

# Part IV — Enabling architecture that makes extreme depth affordable

## 71. The highest-leverage internal primitives

The feature atlas is intentionally much larger than any single release. The way to make it economically tractable is to build a small number of multipliers first.

### A. Frontend architecture multiplier

The current React application should gain:

- a real router with stable nested route semantics;
- a server-state/cache layer rather than bespoke `fetch` state in each screen;
- a generated typed client as the default request path;
- URL-addressable filters, selected objects and workspaces where appropriate;
- a component library for dense operator controls, not only cards/buttons;
- a standard async-operation surface;
- a standard data-grid/view surface;
- a standard inspector/drawer surface;
- a command framework and keyboard shortcut registry;
- a unified toast/notification/error model;
- a rich-document renderer/editor boundary;
- realtime subscription infrastructure where realtime is materially useful.

This is not framework churn for its own sake. It makes the large UI reconstruction feasible without multiplying bespoke state-management behavior.

### B. Operation plan / async job primitive

Many advanced features reduce to the same lifecycle:

1. select target set;
2. validate;
3. compute proposed changes;
4. show blast radius and warnings;
5. obtain approval if required;
6. execute atomically or as a durable job;
7. record per-object outcomes;
8. emit audit/webhooks;
9. allow retry of failed subset;
10. generate a receipt.

Assignment changes, bulk admissions, Event-as-Code apply, award finalization, publication, migration, large exports, extension installs and agent-proposed actions can all reuse this.

### C. Universal query/view primitive

One typed query AST should power:

- organizer filters;
- saved views;
- communications audiences;
- exports;
- bulk operations;
- analytics slices;
- CLI queries;
- MCP references;
- public search subsets where permitted.

This avoids six almost-but-not-quite-compatible filtering systems.

### D. Schema/extension primitive

A registered domain/config type should be able to declare:

- schema;
- human title/help;
- default;
- validation;
- secret fields;
- permissions;
- version;
- migration;
- audit behavior;
- Event-as-Code representation;
- generic UI rendering hints;
- API schema;
- extension ownership.

That is the path from VS42/VS43 into a genuinely extensible platform.

### E. Rich content primitive

One structured content model can support:

- project stories;
- public page rich text;
- sponsor challenge docs;
- event rules;
- announcements;
- feedback summaries;
- custom form help;
- documentation-like resources.

Each context can enable a subset, but security/rendering/accessibility logic should not be independently reinvented.

---

# Part V — Suggested product-depth standard for every subsystem

A subsystem should not be called “finished” merely because CRUD exists. A mature Conflux subsystem should be reviewed across these questions:

1. **Default flow:** Can a first-time user succeed without reading docs?
2. **Power flow:** Can a high-volume operator complete work mostly from keyboard/table/query views?
3. **State model:** Are lifecycle transitions explicit and validated?
4. **Failure model:** Are retries, partial failures, offline behavior and concurrency defined?
5. **History:** Can users answer what changed, by whom, and why?
6. **Preview:** Can high-impact changes be simulated before execution?
7. **Bulk:** Can large events operate on hundreds/thousands of records safely?
8. **Search:** Can users find the records that need attention?
9. **Permissions:** Can access be scoped without giving full organizer power?
10. **Automation:** Is there an API/CLI/MCP representation where it adds value?
11. **Portability:** Can the data/config leave Conflux?
12. **Extensibility:** Can a new provider/type be added without forking core behavior?
13. **Accessibility:** Does the feature preserve keyboard/screen-reader/contrast/text-scaling behavior?
14. **Mobile/on-site:** Does it need a task-specific mobile version rather than responsive desktop?
15. **Performance:** Does it still work at deadline/event scale?
16. **Security:** What untrusted data/external calls/code does it introduce?
17. **Observability:** Can an operator diagnose when it fails?
18. **Reproducibility:** If the feature affects official results, can its inputs/method/version be reconstructed?
19. **Documentation:** Are its invariants and edge cases documented?
20. **Testing:** Are its edge cases encoded as scenarios rather than tribal knowledge?

---

# Part VI — UI reconstruction acceptance bar

The large UI pass should not end because a fixed list of pages was restyled. It should end when a visual/product audit consistently passes the following bar.

## Authenticated application

- Every primary route has a clear dominant task.
- Organizer lists use professional dense data surfaces rather than giant cards.
- Tables, forms, drawers and dialogs share one interaction language.
- Navigation depth remains comprehensible despite feature count.
- Advanced features are discoverable but not permanently visible.
- Keyboard navigation works on high-frequency flows.
- Unsaved work is protected.
- Slow operations become jobs, not frozen buttons.
- Real-time state never causes surprising local data loss.
- Mobile surfaces prioritize on-site tasks rather than reproduce the desktop dashboard.
- No page looks like raw scaffolding with CSS applied afterward.

## Public experience

- Compact hero by default.
- Project/event content appears immediately.
- Typography and media feel deliberate.
- Event themes can vary substantially without breaking hierarchy.
- Gallery and project pages look credible as permanent public artifacts.
- Rich technical content is first-class.
- Pages remain fast and accessible under custom theming.
- Results feel like an intentional publication, not an admin table exposed publicly.

## “No slop” visual audit

For each major surface, explicitly ask:

- Is any container larger than its information warrants?
- Are there nested cards that could become whitespace/borders?
- Is a badge being used where text is better?
- Is color decorative rather than semantic?
- Is an icon redundant?
- Is a hero hiding useful content?
- Is a grid being used where a table would be more efficient?
- Are labels repeated?
- Are controls aligned and consistently sized?
- Does the empty state provide a real next action?
- Does the loading state preserve layout?
- Does the error state preserve user work?
- Does mobile become a coherent task flow?
- Would this screenshot plausibly pass as mature production software without explaining that it was a hackathon project?

If not, the UI pass continues.

---

# Part VII — Product positioning that matches this depth

A future Conflux should be able to make a stronger statement than “open-source Devpost alternative.”

A more defensible product description is:

> **Conflux is a self-hostable operating system for hackathons and technical competitions: deeply customizable event workflows, rich technical submissions, auditable and reproducible judging, serious on-site operations, and one coherent interface across web, API, CLI, Event-as-Code and agents.**

The unusual combination matters:

- Base configuration remains straightforward enough for an ordinary weekend hackathon.
- Technical organizers can model unusual multi-stage events without forking the codebase.
- Judging can be more reproducible and inspectable than conventional event platforms.
- Public pages and project stories can be strong enough to keep permanently.
- On-site operations can be first-class rather than an external spreadsheet stack.
- Event configuration can be reviewed as code.
- Agents can assist through permissioned semantic operations instead of raw database-like CRUD.
- Extensions can add new domain capabilities without collapsing portability and auditability.
- Self-hosting does not mean accepting a rough interface.

That is the direction in which Conflux can plausibly “punch far above its class” as an application rather than merely accumulating an unusually long feature checklist.

---

# Part VIII — Research-derived design notes

## What to borrow from mature systems

### From Devfolio / Linear-style operator UX

Borrow:
- keyboard-first high-volume review;
- undo;
- dense inspection;
- URL-addressable views;
- saved views;
- command bar;
- live collaborator awareness.

Do not borrow:
- product-specific assumptions that narrow Conflux's event model.

### From OpenReview / HotCRP

Borrow:
- reviewer bids/expertise/conflicts;
- matching diagnostics;
- multiple assignment plans;
- rounds;
- rebuttal/meta-review concepts;
- powerful query/bulk operations;
- explicit per-track permissions.

Do not force academic-paper terminology on normal hackathons. These should appear as advanced workflow modules/presets.

### From pretix

Borrow:
- independent check-in lists;
- offline-safe scan reconciliation;
- device/gate metadata;
- badge layouts;
- failed-scan diagnostics.

Do not grow into payments/ticket commerce unless a separate product decision is made.

### From Terraform / Kubernetes

Borrow:
- saved reviewed plan semantics;
- import/adopt;
- semantic moves/renames;
- drift;
- field ownership;
- typed resource schemas;
- overlays;
- strong dry-run/validation.

Do not recreate infrastructure tooling terminology where a domain-specific event term is clearer.

### From Shopify themes

Borrow:
- schema-declared sections/blocks;
- presets;
- defaults;
- nesting;
- reusable global blocks;
- extension blocks;
- locale-aware customization.

Do not allow theme freedom to bypass accessibility/security/performance invariants.

### From modern MCP

Borrow:
- semantic tools;
- resources;
- skills;
- durable tasks;
- explicit authorization;
- structured result links.

Do not expose every CRUD route as an agent tool and call it “agent-native.”

### From GitHub technical Markdown

Borrow:
- familiar Markdown;
- predictable math delimiters;
- fenced code;
- footnotes;
- callouts.

Improve beyond it with:
- explicit versioning;
- judge/public/private sections;
- technical structured blocks;
- submission provenance;
- editor preview;
- accessibility lint;
- archive rendering.

---

# Final conclusion

The repository has already crossed the point where the highest-value strategy is “add the standard missing hackathon features.” Much of that surface exists.

The more ambitious and coherent strategy is:

1. **Stabilize the current system and verification loop.**
2. **Rebuild the UI to a professional product-quality ceiling, using compact/content-first visual design and serious operator interaction patterns.**
3. **Deepen every existing system by adding the missing operational, analytical, versioning, bulk, permission, portability and edge-case layers.**
4. **Build shared primitives so that depth compounds rather than creating hundreds of one-off implementations.**
5. **Make configurability coherent across UI, API, CLI, MCP, Event-as-Code and extensions.**
6. **Keep advanced complexity behind progressive disclosure so the base product remains exceptionally usable.**

The central metric should not be raw feature count. It should be:

> **How many genuinely different event models and operator workflows can Conflux express while the default hackathon still feels simpler, cleaner and more trustworthy than a conventional platform?**

That is a plausible route to making Conflux not just unusually feature-rich, but unusually *deep*.


---

# Part IX — Utility-Filtered Missed Opportunity Pass

**Second-pass date:** 2026-09-29

This pass deliberately uses a stricter inclusion test than the first feature atlas.

The goal is **not** to maximize the number of features. The goal is to find capabilities that:

1. eliminate a real spreadsheet/form/chat/manual workflow organizers already perform;
2. remove repeated work or a common source of event failure;
3. materially improve participant, judge, mentor, sponsor, volunteer, or organizer experience;
4. satisfy a feature people reasonably expect from serious event software;
5. strengthen an existing Conflux subsystem through a natural adjacent workflow; or
6. create a reusable primitive that makes several high-value workflows cheaper.

A feature should generally **not** be added when its primary justification is:

- “the architecture can support it”;
- “it sounds enterprise”;
- “it would be technically impressive”;
- adding verification to already-verifiable verification;
- wrapping an ordinary database fact in another digest/signature/ledger without changing a human workflow;
- adding AI where a deterministic operation is faster and more trustworthy;
- recreating a full external product category when a clean integration solves the problem;
- surveillance or analytics that collect data without a clear operator/participant benefit.

The practical ceiling is therefore not “everything an event could theoretically track.” It is **everything that makes running, participating in, judging, or extending a hackathon materially better.**

## 72. Findings from the second research pass

Several useful gaps stand out after comparing Conflux against current hackathon products, active organizer guidance, and recent participant complaints.

### A. Conflux is deeper than most platforms in competition mechanics, but real-world event operations are still underrepresented

Major League Hacking's organizer guide treats the following as normal hackathon operations:

- food and dietary restrictions;
- swag and prize distribution;
- transportation and travel reimbursement;
- hardware;
- emergency planning;
- help desks;
- detailed run-of-show;
- volunteer duties;
- judge communication and briefing;
- participant reminders;
- code-of-conduct acknowledgement;
- minor forms where needed;
- event closeout.

These are not novelty features. They are exactly the categories that often end up in spreadsheets, Google Forms, Discord channels and paper checklists.

### B. Judging trust is a current participant problem

Recent public hackathon discussions show frustration not merely with scores, but with uncertainty over whether projects were actually reviewed, demos were watched, and judges left any feedback at all.

The useful response is **review process evidence**:

- Was every project assigned enough independent reviews?
- Were all required rubric fields completed?
- Did a judge actually open the frozen project evidence before finalizing?
- Was a required demo artifact marked reviewed?
- Were judge dropouts repaired before results?
- Was feedback captured and released according to policy?

The useful answer is *not* invasive activity surveillance or publishing judges' private behavior.

### C. Current smaller competitors emphasize workflow simplicity around judging

HackHQ's 2026 additions include:

- parallel judging rooms;
- track/challenge scoring;
- top-picks voting;
- custom judge assignment;
- live completion views;
- CSV participant import;
- accountless submission links;
- embedded demo video;
- organizer announcements.

Conflux already has more sophisticated primitives than many of these, but some of the **simple workflow affordances** remain valuable. Sophisticated backend models should make ordinary cases easier, not require advanced configuration.

### D. Sponsors and recurring programs want measurable outcomes

Current platforms increasingly pitch:

- sponsor onboarding;
- challenge adoption;
- participant engagement;
- recruiting pipelines;
- sponsor ROI;
- repeat-event reuse.

This suggests a useful layer above Conflux's sponsor challenges/resources: deliverables, engagement, opt-in talent discovery, and repeat-program reporting.

### E. Event organizers still use separate software for operational tasks

MLH's own software guide references tools for:

- applications;
- RSVPs;
- buses;
- travel reimbursement;
- mentorship queues;
- expo/table assignment;
- judging.

Conflux already owns many of these domains. The remaining useful opportunity is to close the high-friction gaps while resisting the temptation to become a full accounting, travel-booking, messaging, HR, or ticket-commerce suite.

---

# Part X — High-value missed opportunities

## 73. Personalized participant event pass / “My Event” hub

This is one of the most useful missing unification layers.

Instead of making a participant hunt through team, project, resources, schedule and check-in surfaces, provide one compact **My Event** page that answers:

- Am I accepted/confirmed?
- What do I need to do next?
- Who is on my team?
- What stage is my project in?
- When is the next deadline?
- What room/table am I assigned?
- What sessions did I RSVP to?
- What is my QR check-in pass?
- Which rules/waivers still need acknowledgement?
- Do I have unresolved eligibility findings?
- Do I have a mentor booking?
- When/where do I present?
- Has my submission finalized successfully?
- When will judging/results happen?
- Where are venue/travel instructions?

Useful depth:

- BASE — generated checklist ordered by urgency.
- BASE — exact next deadline with event/local timezone.
- BASE — QR event pass.
- BASE — team/project status.
- BASE — venue and check-in information.
- BASE — “you are ready” state when nothing remains.
- ADV — personalized schedule.
- ADV — meal/room/table/badge entitlements where enabled.
- ADV — travel/reimbursement status.
- ADV — accommodation request status.
- ADV — emergency/event contact.
- ADV — offline-friendly mobile version.
- ADV — wallet/pass export if easy to implement cleanly.
- PROG — hub is derived from canonical state; it should not introduce another workflow truth source.

**Why include:** It reduces navigation cost across almost every participant workflow and makes the large feature count feel simpler.

## 74. Staff, judge, mentor, speaker and volunteer recruitment/onboarding

Conflux has role workspaces, but there is value in the workflow *before* someone becomes an active staff member.

- BASE — public/private interest form for judge/mentor/volunteer/speaker.
- BASE — invitation and acceptance/decline.
- BASE — role-specific onboarding checklist.
- BASE — event date/time/location expectations.
- BASE — Code of Conduct/rules acknowledgement.
- ADV — availability windows.
- ADV — expertise/track preferences.
- ADV — role capacity/needed-count target.
- ADV — organizer review/approval.
- ADV — bulk invite.
- ADV — reminder sequence for unconfirmed invitees.
- ADV — waitlist/backup pool.
- ADV — previous-event role history.
- ADV — “confirmed / tentative / declined / no response” dashboard.
- EXPERT — reusable cross-event staff directory.
- EXPERT — suggested judge/mentor candidates from prior events, never automatic outreach.
- PROG — invitation state should feed staffing and judging-readiness calculations.

**Why include:** Judge/mentor recruitment happens before the sophisticated assignment features can help.

## 75. Judge briefing, training and readiness gate

Conflux's judging math is sophisticated enough that judge readiness deserves first-class support.

- BASE — organizer briefing page containing rubric, timing, event philosophy and logistics.
- BASE — judge acknowledgement before first ballot.
- BASE — example scorecard.
- BASE — clear conflict/recusal instructions.
- BASE — judging-location or remote-call instructions.
- ADV — short calibration/example project.
- ADV — “score this example, then compare with anchors.”
- ADV — required briefing completion if organizer enables it.
- ADV — rubric-change acknowledgement when a published judging configuration changes before judging.
- ADV — judge FAQ.
- ADV — one-click report-a-problem/help request from judging workspace.
- ADV — briefing completion/readiness dashboard.
- EXPERT — organizer can require calibration tolerance before assignments are released.
- EXPERT — different briefing modules per judge pool/award.

**Why include:** MLH explicitly recommends a judging debrief because day-of judge process quality is a major failure mode.

## 76. Judge staffing and capacity planner

Conflux can turn its assignment knowledge into pre-event planning.

- BASE — estimate judge count needed from expected projects, reviews/project, minutes/review and judging window.
- BASE — compare required vs confirmed judges.
- BASE — show capacity shortage before judging begins.
- ADV — incorporate track-specific judge requirements.
- ADV — incorporate physical walking/travel time.
- ADV — incorporate judge availability windows.
- ADV — incorporate sponsor/award pools.
- ADV — scenario slider: 100 / 150 / 200 expected projects.
- ADV — no-show reserve recommendation.
- ADV — forecast latest likely completion.
- ADV — “what if 20% more projects submit?” scenario.
- EXPERT — use historical submission/check-in ratio as an optional forecast input.
- EXPERT — Monte Carlo-style dropout sensitivity only if it produces clear staffing recommendations.

**Why include:** This converts existing solver sophistication into a pre-event decision tool organizers can actually use.

## 77. Review coverage and judging-completeness evidence

This is a strong trust feature with a clear use.

For organizers:

- BASE — every project shows required reviews vs completed reviews.
- BASE — every ballot shows complete/incomplete without exposing peer scores to judges.
- BASE — missing rubric criteria highlighted.
- BASE — project with zero completed reviews is impossible to overlook.
- ADV — required demo/evidence checklist marked reviewed.
- ADV — stale/in-progress ballot detection.
- ADV — judge no-show/dropout warnings.
- ADV — deadline projection from current completion rate.
- ADV — auto-suggest rebalancing when coverage is at risk.
- ADV — “unreviewed for X minutes” operations view.
- ADV — finalist cannot silently advance while required coverage is missing unless an authorized override is recorded.
- EXPERT — evidence graph showing which independent completed reviews support each official ranking/award.

For participants, optionally after judging:

- BASE — show number of completed official reviews.
- ADV — show whether required demo/artifact evidence was included in the official frozen review package.
- ADV — release rubric feedback according to event policy.
- ADV — never expose private judge activity timelines or identities unless the event explicitly publishes them.

**Why include:** It directly addresses a common participant trust complaint without adding performative cryptography.

## 78. Judge no-show and live reassignment mode

Normal assignment planning is not enough for real events.

- BASE — mark judge unavailable/no-show.
- BASE — immediately show impacted projects.
- BASE — suggest safe replacement assignments.
- BASE — preserve completed ballots.
- ADV — reserve judge pool.
- ADV — reassign only unfinished obligations.
- ADV — physical-route recalculation.
- ADV — notify affected judge/organizer.
- ADV — restore judge if they return.
- ADV — explain any resulting coverage/connectivity degradation.
- EXPERT — rapid repair plan that minimizes movement and workload disruption while preserving hard constraints.

**Why include:** High-value use of existing assignment algorithms during the exact period organizers are under maximum pressure.

## 79. Demo/pitch queue and presentation timer

Many events have live pitches, finals or scheduled demos in addition to science-fair judging.

- BASE — create demo session/room.
- BASE — ordered team queue.
- BASE — visible current/next team.
- BASE — configurable presentation and Q&A timer.
- BASE — presenter “ready/not ready.”
- ADV — multiple parallel rooms.
- ADV — judge panel per room.
- ADV — delay/reorder controls.
- ADV — screen/projector display mode.
- ADV — participant mobile queue position.
- ADV — automatic “report to staging area” notification.
- ADV — no-show handling.
- ADV — recording/video link attached to presentation slot.
- ADV — finalist queue built directly from deliberation result.
- EXPERT — room balancing from projected duration and judge availability.

**Why include:** It replaces the common spreadsheet + stopwatch + Discord message workflow.

## 80. Event run-of-show and live control timeline

A schedule tells attendees what happens. A **run-of-show** tells organizers what needs to happen behind the scenes.

- BASE — operational timeline separate from public schedule.
- BASE — tasks with owner, due time and status.
- BASE — dependencies.
- BASE — role/team assignment.
- BASE — “happening now / next 30 minutes / overdue.”
- ADV — reusable templates: doors open, meal arrival, submission freeze, judge briefing, judging start, finalists, closing.
- ADV — private notes and contingency instructions.
- ADV — attach runbook/checklist.
- ADV — confirm critical milestones.
- ADV — bulk “mark ready.”
- ADV — last-minute delay shifts downstream target times with preview.
- ADV — communication action linked to milestone.
- ADV — incident linked to timeline.
- EXPERT — rehearsal mode / dry run.
- PROG — timeline hooks can fire deterministic reminders, never autonomous irreversible operations.

**Why include:** This is core event management work and prevents Conflux from stopping at the competition boundary.

## 81. Volunteer shift and duty management

Avoid becoming workforce-management software; solve the event-specific problem.

- BASE — volunteer roles/duties.
- BASE — shifts and availability.
- BASE — assign volunteers.
- BASE — check-in/out of shift.
- BASE — instructions/location.
- ADV — min staffing per duty.
- ADV — shortage warnings.
- ADV — swap/reassignment.
- ADV — mobile “my shift.”
- ADV — role-specific checklists.
- ADV — meal/break windows.
- ADV — emergency-contact escalation.
- ADV — history of completed duties for organizer reference.
- EXPERT — automatically propose assignments from availability/skills.
- PROG — shift state appears in live operations dashboard.

**Why include:** MLH explicitly tells organizers to confirm volunteer duties; large in-person events often run these from sheets.

## 82. Help desk / organizer support queue

Mentor help and operational help are different.

- BASE — attendee can ask a logistics/event question.
- BASE — categories: registration, team, submission, venue, accessibility, technical platform, prize, other.
- BASE — triage/claim/resolve.
- BASE — participant sees status.
- ADV — priority/urgency.
- ADV — location/room.
- ADV — internal note vs participant-visible response.
- ADV — canned answers linked to FAQ.
- ADV — convert repeated issue into announcement/FAQ suggestion.
- ADV — handoff to mentor queue when question is actually technical.
- ADV — organizer SLA and backlog dashboard.
- ADV — Discord/Slack intake adapter if desired.
- EXPERT — outage/banner mode when many tickets share one incident.

**Why include:** This is a real event workflow and naturally reuses the mentor queue primitive.

## 83. Code of Conduct acknowledgement and incident workflow

Conflux has moderation/governance, but event-safety incidents are a distinct operational domain.

- BASE — published Code of Conduct.
- BASE — required acknowledgement at registration/check-in when configured.
- BASE — private incident-report form.
- BASE — named or anonymous reporting depending on event policy.
- BASE — restricted incident visibility to authorized safety staff.
- BASE — status: received / investigating / resolved.
- ADV — severity/category.
- ADV — incident assignment.
- ADV — evidence attachments.
- ADV — protective action notes.
- ADV — attendee restriction/ban integrated with check-in.
- ADV — internal immutable history.
- ADV — emergency contacts/resources.
- ADV — separate public communication from private case record.
- EXPERT — cross-event restriction lists only where the organization has an appropriate policy/legal basis.
- SECURITY — this domain should have stricter access/audit/retention than ordinary moderation.

**Why include:** MLH explicitly requires a clear incident-reporting system and Code of Conduct acknowledgement.

## 84. Minor/guardian forms and participant consent records

Do not build a legal-document platform. Build a clean evidence/requirements workflow.

- BASE — organizer-defined required acknowledgement/consent documents.
- BASE — versioned text/PDF.
- BASE — participant acknowledgement timestamp and document version.
- ADV — guardian-required flag based on configured age rules.
- ADV — guardian contact and completion state.
- ADV — upload externally signed form where required.
- ADV — expiration/re-sign if the document changes materially.
- ADV — check-in blocks only when organizer explicitly configures the document as required.
- ADV — media/photo consent as a separate opt-in/out record.
- ADV — privacy notice acknowledgement.
- EXPERT — external e-signature provider integration instead of implementing legal signatures in core.

**Why include:** Minor forms and participant acknowledgements are common at student events; workflow state matters even when legal signing is external.

## 85. Accessibility accommodation requests

Accessibility should include operational accommodation, not only WCAG.

- BASE — optional accommodation request during registration.
- BASE — free-text and organizer-defined categories.
- BASE — private visibility to designated staff.
- BASE — participant can update request until a configured cutoff.
- ADV — request status and organizer note.
- ADV — accessible seating/location assignment.
- ADV — interpreter/captioning requirement.
- ADV — dietary request linkage where relevant.
- ADV — mobility/access route notes.
- ADV — session-level accommodation needs.
- ADV — individualized check-in instructions.
- EXPERT — aggregate planning counts that hide sensitive details from staff who do not need them.

**Why include:** It improves an actual participant workflow and extends accessibility beyond visual frontend compliance.

## 86. Dietary needs, meal planning and distribution

Do not become catering software; solve the organizer counts and participant entitlement problem.

- BASE — dietary/allergy fields during registration.
- BASE — aggregate counts for authorized organizers.
- BASE — meal schedule.
- ADV — meal entitlement by checked-in status/role.
- ADV — QR/badge meal claim.
- ADV — count remaining/served.
- ADV — dietary label shown only to appropriate distribution staff, not publicly.
- ADV — meal vendor count export.
- ADV — shortage warning from RSVP/check-in counts.
- ADV — organizer can mark special meal pickup.
- ADV — unused/overage estimate for post-event analysis.
- SECURITY — allergy/dietary data gets restricted visibility and retention controls.

**Why include:** Food and dietary planning is explicitly ordinary hackathon work and currently falls outside most competition platforms.

## 87. Travel, buses and reimbursement

This should be bounded and optional.

- BASE — event travel instructions and venue directions.
- BASE — parking/transit information.
- BASE — travel-assistance eligibility policy.
- ADV — attendee reimbursement request.
- ADV — amount/cap based on organizer rules.
- ADV — receipt upload.
- ADV — submitted/approved/paid/rejected status.
- ADV — organizer export to actual finance/payment system.
- ADV — bus/shuttle route and RSVP.
- ADV — seat capacity/waitlist.
- ADV — arrival/departure manifest for organizer.
- ADV — carpool interest as an opt-in discovery field; do not expose exact home addresses.
- ADV — hotel/accommodation instructions and externally managed booking reference.
- EXPERT — external finance provider integration for reimbursement payment.
- DO NOT BUILD — airline/hotel booking engine, payment processor, tax platform.

**Why include:** Hackathon software historically includes travel reimbursement and bus coordination; MLH has explicit travel/reimbursement guidance.

## 88. Hardware lab, loaner and equipment checkout

Especially valuable for hardware, robotics and sponsor-device events.

- BASE — inventory item/type and quantity.
- BASE — checkout/return to participant/team.
- BASE — item identifier/QR.
- BASE — current availability.
- ADV — reservation queue.
- ADV — item condition.
- ADV — due/return reminder.
- ADV — consumable vs returnable.
- ADV — restricted equipment requiring approved training.
- ADV — equipment location.
- ADV — missing/damaged status.
- ADV — per-team quota.
- ADV — sponsor-owned inventory.
- ADV — setup/tutorial linked to equipment.
- EXPERT — lab capacity/time-slot reservation for machines such as laser cutters/3D printers.
- EXPERT — safety acknowledgement before restricted tool use.
- DO NOT BUILD — general asset-management/ERP system.

**Why include:** Hardware resources are a real differentiator for physical events and fit naturally with sponsor resources, check-in and team state.

## 89. Swag, prize inventory and distribution

Prizes already have fulfillment. The same simple inventory primitive can handle event materials.

- BASE — item, variant/size, stock.
- BASE — eligibility group.
- BASE — claimed/unclaimed.
- ADV — size preference at registration.
- ADV — QR/badge claim.
- ADV — prevent duplicate claim.
- ADV — low-stock warning.
- ADV — role-specific packs.
- ADV — sponsor swag allocation.
- ADV — leftover/undistributed count.
- ADV — winner physical prize handoff.
- ADV — shipping-needed flag for remote winners.
- EXPERT — external fulfillment/shipping integration.
- DO NOT BUILD — warehouse management.

**Why include:** Organizers repeatedly track shirts, stickers, packs and physical prizes manually.

## 90. Badge, signage and print center

The onsite subsystem already has enough structured data to generate useful physical artifacts.

- BASE — badge templates by role.
- BASE — participant name + QR + role.
- BASE — print single/reprint.
- BASE — table/project number cards.
- ADV — sponsor/judge/mentor badge styles.
- ADV — session/room signs.
- ADV — judging table labels.
- ADV — dietary/accessibility indicator only where appropriate and privacy-safe.
- ADV — print queue.
- ADV — batch PDF.
- ADV — parking pass templates.
- ADV — emergency/contact cards.
- EXPERT — label-printer adapter.
- PROG — print layouts use canonical event/person/project data.

**Why include:** MLH literally lists badges/lanyards, parking passes, minor forms and table numbers as things organizers prepare.

## 91. Event emergency and incident operations

Separate emergency operations from Code-of-Conduct case management.

- BASE — emergency contact/runbook page for staff.
- BASE — venue emergency instructions.
- BASE — organizer “critical announcement” channel.
- ADV — incident type: medical, fire/alarm, weather, building, network/power, security, other.
- ADV — incident commander/owner.
- ADV — staff-only timeline.
- ADV — impacted rooms/sessions.
- ADV — attach emergency procedure.
- ADV — trigger public/role-scoped announcement with explicit human confirmation.
- ADV — post-incident notes.
- EXPERT — offline printable/exportable emergency pack.
- DO NOT BUILD — emergency dispatch or medical record system.

**Why include:** Emergency planning is ordinary live-event responsibility; Conflux already has communications and onsite state to make it useful.

## 92. Venue readiness / setup checklist

A small feature with large day-of value.

- BASE — reusable event setup checklist.
- BASE — owner/status.
- BASE — room/location.
- BASE — due-by time.
- BASE — items such as Wi-Fi, power, tables, signage, check-in station, judging area, food, AV.
- ADV — photo/evidence attachment where useful.
- ADV — issue/blocker flag.
- ADV — template based on event mode/features.
- ADV — “all critical venue items ready” gate.
- ADV — teardown checklist.
- ADV — post-event venue handback checklist.

**Why include:** It replaces a mundane but high-risk checklist with almost no conceptual overhead.

## 93. Budget, sponsor commitments and event expenses — deliberately narrow scope

A lightweight event budget can remove a major spreadsheet without becoming accounting software.

- BASE — planned budget categories.
- BASE — committed vs actual.
- BASE — sponsor cash/in-kind commitments.
- BASE — event expenses.
- BASE — receipt/document attachment.
- ADV — vendor/expense status: planned/ordered/invoiced/paid.
- ADV — reimbursement linkage.
- ADV — sponsor commitment due date.
- ADV — per-attendee cost.
- ADV — budget variance.
- ADV — category export.
- ADV — read-only finance role.
- EXPERT — accounting/payment integrations via export/API.
- DO NOT BUILD — double-entry accounting, payroll, bank reconciliation, tax preparation.

**Why include:** Every hackathon has a budget, and MLH's own organizer model treats finance as a core organizing function.

## 94. Sponsor pipeline and deliverable tracker

Conflux's sponsor resources/challenges begin after sponsorship exists. Organizers also need to ensure promised deliverables happen.

- BASE — sponsor organization/contact.
- BASE — sponsorship tier/package.
- BASE — committed cash/in-kind value.
- BASE — promised deliverables checklist.
- BASE — challenge/prize/resource links.
- ADV — logo/content deadline.
- ADV — workshop/office-hours slot.
- ADV — judge/mentor seats.
- ADV — booth/table placement.
- ADV — included announcement/email obligations.
- ADV — attendee data-sharing terms represented explicitly; never assumed.
- ADV — fulfillment owner/status.
- ADV — post-event sponsor report.
- ADV — renewal/follow-up reminder.
- EXPERT — import/export to external CRM instead of turning Conflux into Salesforce.
- DO NOT BUILD — full sales CRM pipeline unless later demand proves it belongs.

**Why include:** It connects sponsorship promises to actual event operations and sponsor ROI.

## 95. Sponsor ROI and challenge adoption report

A practical post-event artifact.

- BASE — challenge page views.
- BASE — challenge opt-ins.
- BASE — eligible/submitted projects.
- BASE — awarded projects.
- BASE — workshop attendance.
- ADV — resource link engagement.
- ADV — mentor/office-hours usage for sponsor challenge.
- ADV — project technologies used, based on participant-declared data.
- ADV — participant feedback about sponsor tools.
- ADV — sponsor feedback survey.
- ADV — public result/project links.
- ADV — configurable report branding/export.
- EXPERT — recruiting/product-adoption metrics only with participant consent and clear data provenance.
- DO NOT BUILD — invasive browser/user tracking merely to inflate sponsor metrics.

**Why include:** Current hackathon platforms explicitly market sponsor ROI; this makes sponsorship easier to renew.

## 96. Participant recruiting / talent opt-in

This can be useful if participant-controlled.

- BASE — optional “open to opportunities” profile setting.
- BASE — participants choose which profile fields can be shared.
- BASE — event-specific consent.
- ADV — sponsor/recruiter can filter only consenting participants.
- ADV — bookmarks/shortlists.
- ADV — participant can see which organizations received their profile if the event chooses transparent sharing.
- ADV — follow-up status is optional and private to authorized recruiting staff.
- ADV — opt-out/revoke where legally feasible.
- EXPERT — export to external ATS/CRM.
- DO NOT BUILD — full applicant tracking system.
- DO NOT BUILD — automatic “candidate quality” scoring from hackathon judging results.

**Why include:** Recruiting is a common sponsor/organizer goal, but it should not compromise the competition experience.

## 97. Participant surveys and event feedback

A small general form use can produce high-value event learning.

- BASE — post-event participant survey.
- BASE — judge/mentor/volunteer/sponsor survey variants.
- BASE — anonymous or identified mode.
- BASE — reminder.
- BASE — simple results/CSV.
- ADV — NPS-style question if organizer wants it.
- ADV — session/workshop feedback.
- ADV — sponsor-tool feedback.
- ADV — segment aggregate results by role/track without exposing small sensitive groups.
- ADV — recurring-event comparison.
- ADV — turn common complaints into next-event tasks/templates.
- EXPERT — survey templates attached to event presets.

**Why include:** Serious recurring programs need feedback, and Devpost/competitors explicitly advertise survey/reporting.

## 98. Event closeout workflow

Closing results is not the same as closing the event operationally.

- BASE — winners published.
- BASE — prizes/fulfillment outstanding.
- BASE — reimbursement outstanding.
- BASE — sponsor report outstanding.
- BASE — survey sent.
- BASE — volunteer/judge thank-you communications.
- BASE — archive/export complete.
- ADV — equipment returned.
- ADV — swag/prize leftovers accounted for.
- ADV — incident/helpdesk cases closed.
- ADV — post-event project continuation policy activated.
- ADV — static archive snapshot generated.
- ADV — event metrics frozen into final report.
- ADV — lessons/retrospective notes.
- ADV — clone-next-year action after closeout.
- EXPERT — generated closeout packet for partner organizations.

**Why include:** MLH explicitly treats event closeout as a separate workflow; Conflux has enough source data to make it automatic.

## 99. Participation certificates and verifiable event credentials

This is useful if kept simple.

- BASE — participation certificate for checked-in participants under configured eligibility.
- BASE — winner/finalist/judge/mentor/volunteer certificate templates.
- BASE — unique public verification URL or code.
- BASE — PDF generation.
- ADV — certificate eligibility from canonical attendance/submission/judging state.
- ADV — organizer revoke/correct/reissue.
- ADV — badge/credential metadata export.
- ADV — LinkedIn-friendly share link.
- EXPERT — Open Badges-compatible export if it remains low-complexity.
- DO NOT BUILD — blockchain credentials.
- DO NOT BUILD — layers of signatures over a simple verification URL unless a partner explicitly needs signed portable credentials.

**Why include:** Certificates are commonly requested, easy to derive from state Conflux already owns, and useful to participants/staff.

## 100. Marketing attribution and registration-source tracking

A modest feature, not an ad-tech stack.

- BASE — optional registration-source field.
- BASE — UTM/referral capture.
- ADV — campaign/source funnel: visit → register → confirm → check in → submit.
- ADV — partner/referral link.
- ADV — outreach channel comparison.
- ADV — recurring-event invite cohort.
- ADV — public event page conversion.
- EXPERT — privacy-preserving aggregate reporting.
- DO NOT BUILD — cross-site tracking/fingerprinting.
- DO NOT BUILD — marketing automation suite.

**Why include:** Organizers need to know whether outreach worked; recurring programs especially benefit.

## 101. Referral / ambassador links

This is useful only as a thin layer over attribution.

- BASE — organizer can issue a referral link to a club/community/ambassador.
- BASE — count registrations and confirmed attendees from that source.
- ADV — optional referral leaderboard if event culture benefits from it.
- ADV — source-specific landing copy.
- ADV — prevent incentives from altering admission/judging.
- DO NOT BUILD — multi-level referral/affiliate system.

**Why include:** It can help campus/community hackathons grow without becoming marketing-tech bloat.

## 102. Rules and originality disclosure package

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

## 103. Contribution roles / team contribution record

Useful for judging and recruiting when participant-controlled.

- BASE — team members list roles/contributions.
- BASE — contribution statement frozen with submission.
- ADV — per-member technical/design/research/demo contributions.
- ADV — participant confirmation that team statement is accurate.
- ADV — organizer clarification if a prize is individual or role-restricted.
- EXPERT — repository contribution metadata can be shown only as supporting evidence; do not equate commit count with contribution quality.
- DO NOT BUILD — algorithmic “who really did the work” scoring.

**Why include:** Helps judges understand team composition and reduces ambiguity for prizes/recruiting.

## 104. Demo evidence checklist and pitch readiness

The project authoring system can help teams present the work judges actually need to see.

- BASE — event-defined required demo duration/format.
- BASE — upload/link video.
- BASE — project preflight says whether demo evidence is present.
- ADV — checklist from judging criteria: core flow, technical architecture, limitation disclosure, sponsor requirement.
- ADV — video duration validation.
- ADV — transcript/captions supplied by participant/provider where available.
- ADV — judge can mark demo artifact reviewed.
- ADV — exact demo URL/version frozen with submission.
- EXPERT — participant “judge preview” mode that shows exactly what a judge sees.

**Why include:** MLH recommends short demo videos specifically to improve judging; recent participant complaints show why evidence visibility matters.

## 105. Live result incident / correction playbook

Results publication is high-stakes enough for a dedicated recovery workflow.

- BASE — pre-publish preview.
- BASE — atomic publish.
- BASE — rollback visibility if publication fails before becoming official.
- BASE — correction workflow after official publication.
- ADV — affected award/project list.
- ADV — correction reason.
- ADV — participant notification plan.
- ADV — public correction notice.
- ADV — archive retains previous result version.
- ADV — prize-fulfillment hold when result is disputed/corrected.
- EXPERT — rehearse publication against a demo/rehearsal event.

**Why include:** Prevents the worst possible “live projector + wrong winners” scenario and reuses existing publication/audit primitives.

## 106. Event change impact and notification assistant

When organizers change dates, rooms, requirements or rules, the system should identify affected people/workflows.

- BASE — configuration change preview says what operational state is impacted.
- ADV — identify participant cohorts affected by deadline/location/schedule change.
- ADV — suggest audience for notification.
- ADV — show existing scheduled communications that became stale.
- ADV — identify Event-as-Code docs/public pages that reference old value.
- ADV — require explicit acknowledgement for high-impact live-event change.
- ADV — create draft announcement from structured change facts; human edits/sends it.
- EXPERT — dependency graph across event config, pages, schedule, policies and integrations.

**Why include:** MLH explicitly emphasizes communicating major event changes quickly; Conflux has the domain data to automate the tedious impact discovery.

## 107. Recurring event edition / year-over-year comparison

Conflux already has cloning and cross-event history; add a practical recurring-program workflow.

- BASE — “create next edition from this event.”
- BASE — explicit carry-over selection.
- BASE — preserved sponsor/judge/template references where appropriate.
- ADV — compare registration, attendance, submission and judging metrics across editions.
- ADV — compare sponsor challenge adoption.
- ADV — reused vs changed rules/rubrics.
- ADV — copy public pages as drafts with stale-date/link warnings.
- ADV — invite prior judges/mentors/participants selectively.
- ADV — prior-year project archive stays separate.
- EXPERT — organization program dashboard for a recurring series.

**Why include:** Repeat events are common, and recurring setup is where deep configuration can repay itself.

## 108. Public event changelog

A small transparency feature for events with evolving rules/schedule.

- BASE — important organizer changes can optionally be published as a changelog entry.
- BASE — date/time and summary.
- ADV — link to affected rule/schedule/page.
- ADV — “substantive” vs “minor wording” classification.
- ADV — participants can subscribe to changes.
- ADV — auto-draft from a semantic configuration diff.
- DO NOT BUILD — publish every internal audit event.

**Why include:** Participants care when rules/deadlines change, not about internal CRUD logs.

## 109. Participant-facing notification center with actionability

The first pass included notifications; this adds a stronger usefulness requirement.

Every notification should preferably answer:

- What happened?
- Does it require me to act?
- By when?
- Where do I act?
- Can it be safely dismissed?

Useful types:

- team invite;
- application decision;
- waitlist promotion;
- missing RSVP;
- rule acknowledgement;
- submission issue;
- eligibility remediation;
- mentor booking;
- room/table assignment;
- schedule/location change;
- judge assignment;
- feedback released;
- prize fulfillment action.

Avoid:

- noisy “someone viewed your project” activity;
- meaningless engagement gamification;
- duplicated email + banner + inbox messages with no preference controls.

## 110. Calendar and reminder integration

A practical cross-cutting feature.

- BASE — add event and key deadlines to calendar.
- BASE — event timezone embedded correctly.
- ADV — personal schedule iCalendar feed.
- ADV — judge assignment/calendar feed.
- ADV — mentor office-hours calendar.
- ADV — organizer run-of-show calendar.
- ADV — change/cancel updates propagate.
- ADV — configurable reminder preference.
- EXPERT — Google/Microsoft calendar integration only if needed beyond standards-based iCalendar.

**Why include:** Deadlines, sessions and judging windows are time-driven; calendar export is an expected convenience.

## 111. Searchable event knowledge base / FAQ with operational linkage

Conflux already has public Q&A/resources; connect them more tightly to operations.

- BASE — searchable FAQ.
- BASE — organizer-authored canonical answer.
- BASE — public/private audience.
- ADV — help-desk response can link/promote an answer.
- ADV — repeated help requests suggest FAQ gap.
- ADV — sponsor challenge FAQ belongs to sponsor context.
- ADV — rules FAQ links to exact rule.
- ADV — version/update timestamp.
- ADV — participant sees relevant FAQs based on current workflow.
- EXPERT — semantic search can be optional, with deterministic full-text search remaining baseline.

**Why include:** Reduces organizer support load without building a chatbot as the primary answer surface.

## 112. Announcement acknowledgement for critical operational messages

Not every announcement needs it, but sometimes organizers need to know who received a venue/deadline/safety change.

- ADV — announcement can be marked “acknowledgement required.”
- ADV — target audience snapshot.
- ADV — completion list.
- ADV — reminder only to unacknowledged recipients.
- ADV — deadline.
- ADV — used sparingly for rules/safety/location changes.
- DO NOT BUILD — read receipts for every message.

**Why include:** Turns critical communication into a closed-loop workflow.

## 113. Event-specific document/resource center

Useful resources should not be scattered across FAQ, pages, sponsor blocks and messages.

- BASE — organized resources by category.
- BASE — visibility by role/stage.
- BASE — file/link/title/description.
- ADV — version/update timestamp.
- ADV — pin critical resources.
- ADV — acknowledgement requirement when appropriate.
- ADV — downloadable offline event pack.
- ADV — resource health/link checker.
- ADV — archive resources with event.
- ADV — per-track/sponsor resources.

**Why include:** Simplifies event resource discovery and naturally reuses page/resource primitives.

## 114. Speaker/workshop operator workflow

Schedule already covers sessions; add the practical management layer.

- BASE — speaker profile/contact.
- BASE — session assignment.
- BASE — confirmation status.
- BASE — arrival/check-in information.
- ADV — slide/resource upload.
- ADV — AV requirements.
- ADV — room capacity.
- ADV — host/moderator assignment.
- ADV — reminder.
- ADV — recording/publication permission.
- ADV — session feedback.
- DO NOT BUILD — full conference speaker management suite.

**Why include:** Hackathons routinely run technical workshops, sponsor demos and opening/closing talks.

## 115. Prize claim and winner support inbox

Prize fulfillment can become a participant-friendly workflow.

- BASE — winner sees prize, status and required next action.
- BASE — secure contact/update form.
- ADV — required shipping/payment info fields determined by prize type.
- ADV — document request through external provider where sensitive.
- ADV — claim deadline.
- ADV — organizer/sponsor note.
- ADV — missing information reminder.
- ADV — support ticket linked to award.
- ADV — shipped/sent/claimed status.
- ADV — correction/alternate winner handling.
- SECURITY — minimize storage of sensitive financial/tax data; integrate rather than retain when possible.

**Why include:** Winning should not drop users into an email thread maze.

## 116. Event “doctor” and operator readiness diagnostics

This should go beyond deployment health.

One command/page could inspect:

- missing event dates;
- contradictory deadlines;
- no published rules;
- no registration path;
- prize without selection method;
- award with no eligible projects;
- judge capacity shortage;
- disconnected assignment graph;
- judge conflicts unresolved;
- unpublished rubric;
- required submission field not exposed;
- broken public links/media;
- page block with inaccessible contrast;
- venue rooms over capacity;
- checked-in attendees without necessary consent;
- scheduled announcement with empty audience;
- webhook failures;
- backup too old;
- stale sponsor resource;
- results publication approval incomplete.

**Why include:** This is the useful version of “verification depth”: it catches actual event failures.

## 117. What-if simulator for event operations

A generalized “what if?” surface can reuse existing planning primitives.

Useful questions:

- What if submissions are 30% higher than expected?
- What if 4 judges cancel?
- What if registration capacity changes from 500 to 600?
- What if judging shrinks from 180 to 120 minutes?
- What if we move the deadline by 30 minutes?
- What if a sponsor challenge requires a new artifact?
- What if one room becomes unavailable?
- What if a track has twice the expected projects?
- What if we prohibit projects from winning more than one sponsor award?

The output should show:

- affected people/projects;
- infeasible constraints;
- extra staffing/capacity;
- changed communication audience;
- expected judging workload;
- resulting award/eligibility changes where deterministic.

**Why include:** Conflux already has the underlying models; this makes them decision support rather than configuration machinery.

## 118. Saved operational playbooks

For recurring organizers, capture proven procedures without building a generic workflow engine.

Examples:

- “open registration”;
- “one week before event”;
- “doors open”;
- “submission deadline”;
- “start judging”;
- “judge no-show”;
- “publish winners”;
- “event closeout.”

A playbook can include:

- checklist tasks;
- links to Conflux actions/views;
- draft communications;
- required approvals;
- responsible roles;
- expected evidence.

**Why include:** Converts tacit organizer knowledge into reusable operating procedure.

## 119. Lightweight organizer decision log

Not every important event decision is a configuration mutation.

- ADV — organizer can create a short decision record.
- ADV — question/context, decision, reason, owner and date.
- ADV — link affected rule/config/page/incident.
- ADV — internal only by default.
- ADV — mark decision as temporary / revisit after event.
- ADV — include in event retrospective.
- DO NOT BUILD — force documentation of trivial actions.

**Why include:** Useful for multi-person organizing teams and reduces “why did we do this?” confusion.

## 120. Event retrospective and next-edition handoff

A practical closeout artifact.

- BASE — what worked / what failed / metrics.
- ADV — incidents and bottlenecks automatically linked.
- ADV — judge staffing actual vs plan.
- ADV — submission surge actual vs forecast.
- ADV — sponsor/mentor utilization.
- ADV — help-desk top categories.
- ADV — participant survey themes.
- ADV — unresolved tasks carried into next edition.
- ADV — recommended template/config updates as *drafts*, not auto-applied.
- ADV — create next-edition backlog.

**Why include:** Makes Conflux valuable between events, not just during one.

---

# Part XI — Workflow optimizations to deepen existing systems

These are generally more valuable than adding a new top-level module.

## 121. Progressive-disclosure organizer mode

Given Conflux's eventual feature depth:

- default navigation only shows enabled systems;
- setup wizard asks intent, then enables relevant modules;
- advanced controls remain under explicit “Advanced” disclosure;
- expert features can be pinned by frequent users;
- settings search jumps directly to hidden configuration;
- command palette exposes power operations without cluttering every page;
- documentation/help links are contextual.

**Outcome:** extreme capability without intimidating first-time organizers.

## 122. Context-preserving deep links

Every high-frequency organizer/judge state should be linkable:

- event;
- selected tab/view;
- filter;
- selected project/participant;
- stage;
- judging plan;
- audit event;
- saved view.

Avoid encoding volatile unsaved sensitive data in URLs.

**Outcome:** easier collaboration, support and incident response.

## 123. “Open in split view” everywhere it saves navigation

Useful examples:

- participant table → profile/application;
- project table → submission/evidence;
- judge table → workload/conflicts;
- awards table → candidate evidence;
- help desk → participant/project;
- sponsor challenge → eligible projects.

**Outcome:** operator throughput without huge screen redesigns.

## 124. Safe undo / compensate where the domain supports it

Not every change can be rolled back, but many can:

- wrong application decision before downstream action;
- wrong tag;
- accidental team assignment;
- schedule move;
- hidden project;
- notification draft;
- unpublished page edit.

Where irreversible, say so *before* execution.

**Outcome:** users move faster when small mistakes are recoverable.

## 125. Smart default views

Instead of dumping all entities:

- participants → “Needs action” first;
- projects → “Incomplete / eligibility issue / finalized” status;
- judging → “At risk / incomplete” first;
- awards → “Unresolved” first;
- mentor queue → “Unclaimed urgent” first;
- webhooks → “Failing” first.

**Outcome:** Conflux becomes an operations tool rather than a database browser.

## 126. Batch setup from CSV with mapping preview

Useful for:

- participants;
- judges;
- mentors;
- sponsors;
- tracks;
- rooms;
- inventory;
- staff.

Must have:

- mapping preview;
- validation;
- duplicate strategy;
- dry-run;
- error CSV;
- idempotent re-import strategy.

**Outcome:** migration from spreadsheets becomes frictionless.

## 127. Clone-and-edit instead of recreate

Apply consistently to:

- rubric;
- award;
- form;
- policy;
- communication;
- page;
- session;
- sponsor challenge;
- view;
- template;
- check-in list.

**Outcome:** repeated event configuration becomes much faster.

## 128. Inline validation at the point of configuration

Examples:

- impossible deadline order;
- award with no eligible scope;
- judge pool too small;
- contrast failure;
- empty communication audience;
- room capacity exceeded;
- form condition referencing nonexistent field;
- Event-as-Code unmanaged/prune hazard.

**Outcome:** errors are fixed where they are created rather than discovered at launch.

## 129. Default presets for sophisticated systems

Complexity should arrive with good presets:

- judging: weighted rubric, top-picks, pairwise, hybrid;
- assignment: balanced, expertise-aware, physical science-fair;
- admissions: open, approval, waitlist;
- event: online, hybrid, in-person;
- publication: immediate, scheduled, approval-required;
- feedback: private, anonymous release, named release;
- page: simple, sponsor-heavy, technical challenge.

**Outcome:** advanced backend features become usable by ordinary organizers.

## 130. Human-readable explanations everywhere a solver/policy decides something

Not giant proofs. Useful explanations:

- “Assigned because this judge matches AI track, has capacity, and no conflict.”
- “Project cannot enter award because challenge opt-in was not finalized.”
- “Event-as-Code apply would remove 3 unmanaged pages only with prune.”
- “Participant is blocked from check-in because required waiver v3 is incomplete.”
- “This judge route is infeasible because two assigned projects overlap the same 10-minute window.”

**Outcome:** algorithmic depth creates trust instead of opacity.

---

# Part XII — Useful features to explicitly *not* prioritize

The existence of a powerful architecture makes restraint important.

## 131. Low-value verification recursion

Avoid:

- hash of an already immutable hash merely to produce another layer;
- multiple redundant signatures over data that already has an authenticated canonical source;
- blockchain/notarization for ordinary submissions;
- cryptographic ceremony that no participant, organizer, auditor or integration consumes;
- permanent proofs for ephemeral UI state.

Add cryptographic machinery only when it enables:

- offline verification;
- portable audit;
- tamper-evident external handoff;
- signed credential/archive required by a real consumer.

## 132. Built-in generic chat

Conflux needs:

- announcements;
- inbox/direct operational messages;
- Q&A;
- mentor/help queues.

It does not need to reproduce:

- Discord;
- Slack;
- threaded community servers;
- voice/video rooms.

Integrate with those systems.

## 133. Full accounting / banking

Useful:

- event budget;
- sponsorship commitments;
- expense status;
- reimbursement request/export.

Not useful in core:

- bank connections;
- reconciliation;
- payroll;
- bookkeeping ledger;
- tax filing.

## 134. Full travel booking

Useful:

- travel instructions;
- buses/shuttles;
- reimbursement;
- external booking references.

Do not build:

- airfare search;
- hotel inventory;
- booking/payment engine.

## 135. Full recruiting ATS

Useful:

- participant opt-in;
- consented profile access;
- shortlists;
- export/integration.

Do not build:

- interview scheduling suite;
- candidate ranking model;
- employment offer workflow.

## 136. AI for deterministic tasks

Do not use LLMs for:

- calculating scores;
- enforcing deadlines;
- validating required fields;
- assigning permissions;
- applying policy;
- determining official winners.

AI can assist with:

- drafting organizer communication;
- summarizing open help-desk themes;
- translating or reformatting content;
- proposing configuration from a natural-language brief;
- helping inspect a large event through permissioned MCP.

Official state remains deterministic and reviewable.

## 137. Participant surveillance

Avoid:

- keystroke logging;
- IDE tracking;
- screen recording;
- arbitrary browser fingerprinting;
- judging “effort” from commit counts;
- covert sponsor/recruiter tracking.

Use explicit evidence and declarations.

## 138. Gamification without an event purpose

Avoid adding:

- organizer XP;
- participant streaks;
- arbitrary badges for clicking around;
- engagement scores;
- leaderboards unrelated to event goals.

Useful gamification can exist only when the event deliberately wants it, such as optional referral or mini-event mechanics.

## 139. Generic no-code workflow engine

Conflux already has stages, policies, forms, approvals, Event-as-Code and extensions.

Do not add a second free-form Zapier-like internal workflow engine unless real use cases cannot be represented by those primitives.

## 140. Feature duplication across UI/API/CLI/MCP

A command/tool is not a new feature if the domain capability already exists.

Prefer:

- one canonical service/domain operation;
- multiple interfaces over it.

Avoid:

- UI-only behavior;
- CLI-only mutation semantics;
- MCP-only shortcuts that bypass normal validation.

---

# Part XIII — Strongest second-pass additions

If the goal is to choose the additions with the best ratio of usefulness to complexity, these stand out.

## Tier A — high-value, natural Conflux extensions

1. Personalized participant “My Event” hub.
2. Judge/staff recruitment, invitation and readiness.
3. Judge capacity planner.
4. Review coverage / judging completeness evidence.
5. Judge no-show live repair.
6. Demo/pitch queue + timer.
7. Live run-of-show.
8. Volunteer shift management.
9. Organizer help desk.
10. Accessibility accommodation requests.
11. Code of Conduct / incident workflow.
12. Event closeout.
13. Event doctor/readiness diagnostics.
14. What-if simulator.
15. Rules/originality/AI-use disclosures.
16. Event change impact + notification assistant.
17. Calendar integration.
18. Recurring-edition workflow.

These either reuse existing Conflux primitives heavily or directly eliminate a high-friction hackathon workflow.

## Tier B — extremely useful for in-person/student events

19. Dietary/meal planning.
20. Travel/bus/reimbursement workflow.
21. Hardware checkout.
22. Swag inventory/distribution.
23. Badge/signage print center.
24. Minor/guardian consent state.
25. Venue readiness checklist.
26. Emergency operations.
27. Speaker/workshop management.

These should be modular so an online event never sees them.

## Tier C — valuable for mature sponsors/programs

28. Sponsor deliverable tracker.
29. Sponsor ROI report.
30. Participant recruiting opt-in.
31. Participant/staff/sponsor surveys.
32. Lightweight event budget.
33. Participation certificates/credentials.
34. Marketing attribution/referral.
35. Retrospective + next-edition handoff.

These improve recurring-program economics and professionalism but should not dominate the core competition UI.

---

# Part XIV — Revised strategic interpretation

After the second pass, the strongest possible Conflux is broader than “advanced hackathon judging software” but narrower than “generic event ERP.”

A useful boundary is:

> **Conflux should own workflows whose meaning depends on hackathon state.**

Examples:

- travel reimbursement is worth owning when eligibility depends on event attendance and attendee status;
- meal distribution is worth owning when it uses check-in and dietary state;
- volunteer shifts are worth owning when they operate event desks, judging rooms and mentorship;
- sponsor ROI is worth owning when it comes from challenge participation, projects, workshops and awards;
- certificates are worth owning when eligibility comes from attendance/submission/role state;
- recruiting opt-in is worth owning when it connects participants/projects to sponsor relationships;
- run-of-show is worth owning when milestones are submission deadlines, judging, results and event operations.

By contrast, Conflux should generally **integrate rather than own** generic domains such as payroll, airline booking, accounting, Slack-style chat, ATS pipelines and payment processing.

That boundary produces a product that can become exceptionally deep without becoming incoherent.

---

# Research basis for this pass

The following current sources materially informed the pass:

- MLH Hackathon Organizer Guide — operational coverage including registration, food/dietary needs, travel, hardware, emergency planning, judging, scheduling, mentorship, help desk and after-event work:
  https://github.com/MLH/mlh-hackathon-organizer-guide
- MLH Judging Plan — science-fair judging, judge-capacity planning, judging debrief and help path:
  https://github.com/MLH/mlh-hackathon-organizer-guide/blob/master/general-information/judging-and-submissions/judging-plan.md
- MLH Community Values — Code of Conduct, incident reporting, minors/safeguarding, food and event safety expectations:
  https://github.com/MLH/mlh-hackathon-organizer-guide/blob/master/overview/mlh-community-values.md
- MLH Registration guidance — dietary and participant fields:
  https://github.com/MLH/mlh-hackathon-organizer-guide/blob/master/general-information/managing-registrations/registrations.md
- MLH Rules guidance — prior work, crossposting, code/framework and AI-use disclosure:
  https://github.com/MLH/mlh-hackathon-organizer-guide/blob/master/general-information/judging-and-submissions/rules-for-your-hackathon.md
- MLH software guide — existing hackathon tools historically cover buses, travel reimbursement, mentorship queues and expo/judging:
  https://github.com/MLH/mlh-hackathon-organizer-guide/blob/master/organizer-resources/software-for-hackathons.md
- HackHQ 2026 updates/features — judging rooms, top-picks voting, custom assignments, announcements, CSV participant import and submission/video workflows:
  https://hackhq.io/updates
  https://hackhq.io/features
- TAIKAI — current platform emphasis on team matching, event timeline, internal communication, livestreaming and MCP:
  https://taikai.network/
- Devpost for Teams — organizer reporting, team formation, judging, external guests and enterprise access controls:
  https://info.devpost.com/product/devpost-for-teams
- BuilderBase — sponsor onboarding/ROI, live ops, recruiting and repeat-program positioning:
  https://builderbase.com/
- Recent participant discussion about opaque judging and missing review/feedback evidence:
  https://www.reddit.com/r/Devvit/comments/1vrvai6/everything_wrong_with_the_reddit_games_hackathons/

