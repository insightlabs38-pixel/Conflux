# PD-F002 — Feature depth should compound through shared primitives

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §2  
**Queue batches:** PD-F002-B01, PD-F002-B02, PD-F002-B03

## Completion interpretation

This specification is the canonical depth contract for §2. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Shared primitives are platform contracts, not helper functions. Each must define canonical state, lifecycle, authorization, idempotency/concurrency behavior, error shape, extension boundary and migration policy before dependents rely on it.
- Dependents must import/reuse these primitives rather than recreating similar local abstractions.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `DATA_GRID`
- `PREVIEW_CONTEXT`
- `QUERY`
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

## Batch scope

### PD-F002-B01 — Feature depth should compound through shared primitives — Universal entity query/filter engine → Generic event timeline/scheduling primi…

- Shared primitive: Universal entity query/filter engine
- Shared primitive: Saved views and sharable view URLs
- Shared primitive: Configurable dense data-grid primitive
- Shared primitive: Bulk-operation planner with dry-run, impact preview, execution receipt, retry and rollback/compensation semanti…
- Shared primitive: Generic async-job/task model with progress, cancellation, logs, artifacts and durable results
- Shared primitive: Generic approval/gate model
- Shared primitive: Generic comments/notes/mentions/thread model with explicit visibility
- Shared primitive: Generic event timeline/scheduling primitive

### PD-F002-B02 — Feature depth should compound through shared primitives — Generic schema-driven form/config editor → Generic extension manifest/capability m…

- Shared primitive: Generic schema-driven form/config editor
- Shared primitive: Generic rich technical content renderer/editor
- Shared primitive: Generic file/artifact preview pipeline
- Shared primitive: Generic notification/subscription preference model
- Shared primitive: Generic version/diff model for mutable configuration and content
- Shared primitive: Generic policy/explanation model
- Shared primitive: Generic audit provenance envelope
- Shared primitive: Generic extension manifest/capability model

### PD-F002-B03 — Feature depth should compound through shared primitives — Generic “preview as role / as of time / as frozen version” infra…

- Shared primitive: Generic “preview as role / as of time / as frozen version” infrastructure


## PD-F002-B01 canonical contract (T00, 2026-09-30)

Evidence for every statement about current behavior: `docs/verification/PD-F002-B01/T00-census.log` (`probe_census.py`, read-only, run against the live stack). Escalation for the architecture decisions below: `docs/execution-v3/escalations/ESC-20260930-004.yaml` (resolved with the conservative default).

### What exists today (census)

- **Filtering is ad hoc.** 15 view modules read their own `query_params` (`status`, `q`, `offset`, `state`, `timeline`, ...); `core/pagination.py` gives bounded limit/offset with `X-Total-Count`/`Link` headers to a few. There is no shared filter grammar, no sort contract and no entity catalogue. `SavedPublicSearch` stores one public gallery filter blob for anonymous search only.
- **Bulk planning exists**, domain-specific: `communications/bulk.py` (`run_bulk`) plans five actions in a rolled-back transaction, returns exact effects and a signed 600 s preview token, re-validates on apply (409 on drift), applies atomically, audits each action and stores a `BulkReceipt`; re-applying a token replays the saved result. `core/idempotency.py` dedupes unsafe requests by `Idempotency-Key`.
- **No job model.** Celery runs three tasks (webhook delivery, reminders, artifact scanning) with two beat entries; `src/api/jobs/` is an empty directory; long operations (archive export, imports, simulation) run inside the request or a management command. The web has a client-side `useOperation` contract (PD-B04) but nothing durable behind it.
- **No approvals.** The nearest things are `EligibilityReview` (a per-project decision) and `TemporalGate` (a time window).
- **Four unrelated note/comment models** with different semantics: `community.Comment` (public, moderated), `deliberation.DeliberationNote` (private to a room), `projects.MentorNote`, `communications.Message` (broadcast). None is generic, none has explicit audiences or mentions.
- **Time is scattered** over `Event.starts_at/ends_at`, `TemporalGate`, `AgendaSession`, `PublicationSchedule`, stage data and reminders; nothing presents or checks them together.
- **Web tables** are hand-written (`<table>` in 9 components, one shared `cx-table` wrapper), with no sorting, column, density or keyboard contract.

### Shape decisions for all eight primitives

1. **Where they live.** Server code in the `core` app, web code in `src/web/lib` and `src/web/components` (the batch's owned paths). `core` never imports domain apps: a domain registers what it offers (entities, bulk actions, job kinds, approval policies, timeline providers, thread audiences) from its own module at import time, and `core` resolves the workspace with the function-level imports `core.mixins` and `core.authz` already use and the event with `apps.get_model("events", "Event")`. This is the dependency inversion ESC-20260930-002 noted.
2. **Registry-first.** Every primitive is a typed registry plus one generic endpoint family, not a set of helpers. Registered definitions are code (versioned with the app); only user state with lifecycle meaning is stored (saved views, jobs, approvals, threads). Timeline and query results are derived, never stored.
3. **Authorization is decided once, in the registration.** A definition names the roles that may use it and supplies the base queryset/scope; generic code adds nothing, widens nothing and never trusts client-supplied ids, columns, fields or audiences. Hiding in the UI is never authorization.
4. **Error shape.** Validation errors are DRF 400 bodies keyed by the path of the offending part (`filter.and[1].op`); stale or conflicting state is 409 with a machine `code`; refusals carry the same `{code, message}` shape as `eventconfig` Reasons and consequences (POLICY_EXPLAIN in F002-B02 absorbs it).
5. **Idempotency/concurrency.** Mutating primitive endpoints accept `Idempotency-Key` (existing mixin); state machines (job, approval) change status with `select_for_update` and only along their declared transitions; replays return the saved outcome.
6. **Audit.** Every stored-state change records an `AuditEvent` (actor, action, target, before/after where meaningful); reads are not audited.
7. **Migration policy.** All new tables are additive; no existing table or endpoint changes shape. Existing near-primitives stay and are named as adapters or legacy (below). Consumers adopt a primitive by registering against it; nothing is bulk-migrated in this batch.

### Per-primitive contract

| Primitive (task) | Canonical state and lifecycle | Authority boundary | Reuse and migration |
|---|---|---|---|
| `QUERY` (T01) | Versioned JSON AST `{v:1, filter, sort, columns?}`; `filter` is `and`/`or`/`not` over `{field, op, value}`; ops by field type (text: eq, ne, in, contains, startswith; number/date: eq, ne, lt, lte, gt, gte, between, in; bool: eq; enum: eq, in; any: is_null); limits depth 4, 20 predicates, `in` 50, strings 200; sort up to 3 keys plus primary-key tiebreak. Stateless. | An `Entity` registration names key, label, roles, `base(event, user)` queryset, and fields (type, column, label, sortable, filterable, choices). Only registered fields/ops compile; unknown or mistyped parts are 400 with the path; no ORM lookups, traversals or raw SQL are reachable. `GET .../events/{e}/entities/{entity}/` (filter, sort, limit, offset, columns) returns `{entity, total, limit, offset, columns, rows}`. | Reuses `core.pagination` limits. First entities: `applications` and `projects`. The 15 ad-hoc parameter sites keep working unchanged and are listed as adopters; new list features must use QUERY. |
| `SAVED_VIEWS` (T02) | `SavedView` (workspace, event, entity, name, query AST incl. sort, visible columns and density, `visibility` private or organizers, owner, version, timestamps); unique per owner, event, entity and name. Stores a definition, never rows. | Running a view always goes through QUERY under the **viewer's** authorization, so sharing a view cannot expose data; private views are visible to the owner only; changes and visibility flips are audited. URL form is `?view=<id>` or the inline canonical `?filter=` (compact, sorted-key JSON) on the PD-B04 URL-state rules. | Adds `ViewBar` (pick, save, save as, rename, delete, share, copy link). `SavedPublicSearch` stays as the anonymous public-search store (different audience); its filter blob is a later QUERY adopter. |
| `DATA_GRID` (T03) | Web component. Column definitions, server-driven sort, filter and paging state (URL and saved view), visible columns, density (compact or comfortable), row selection; states loading, empty, filtered-empty, error with retry, permission-denied. | Renders only what the server returned; selection is ids the server returned; never sorts or filters the full set in the browser. Accessible table semantics (`aria-sort`, sticky header, keyboard navigation with roving focus, row selection via checkboxes) and a narrow-screen layout. | Composes `LoadingState`, `EmptyState`, `ErrorState`, `useUrlParam`, `useLoad`. First adopters: the applications and projects lists. The nine hand-written tables keep working and adopt when their feature is next touched. |
| `BULK_PLAN` (T04) | The existing planner is the contract: plan (rolled back) returns exact effects and a signed token with TTL; apply re-validates (409 on drift), is atomic, audited per action, idempotent by token, and stored as `BulkReceipt`. T04 adds an action registry seam (`register_action`) so domains add actions without editing `bulk.py`, receipt listing/reading, and the web `BulkPlanner`. | Targets must belong to the event; limits (20 operations, 100 targets each, 1,000 effects) and archived-event refusal stay. Rollback is whole-batch atomic; **compensation after apply is not generic** and is recorded as a limitation, not simulated. | Keeps `communications/bulk.py` and its endpoint and token format; the five actions move behind the registry without changing behavior. `BulkPlanner` consumes DATA_GRID selection and `ConsequenceDialog`-style impact lists. |
| `ASYNC_JOB` (T05) | `Job` (workspace, event, kind, status `queued`, `running`, `succeeded`, `failed`, `cancelling`, `cancelled`, progress done/total/message, params, bounded result, artifact references, requested_by, idempotency key, attempts, heartbeat, timestamps) and `JobLog` (bounded, 500 lines). Transitions only forward along the declared graph under row lock. A Celery task runs a registered handler with a context (`progress`, `log`, `cancelled`); a beat sweep fails jobs with no heartbeat (`timeout`). | Kinds are registered code with a params schema and roles; a caller sees own jobs, organizers see the event's; cancellation is cooperative and never kills work mid-write. Results are durable and bounded; secrets never enter params, logs or results. `GET jobs/`, `GET jobs/{id}/`, `POST jobs/{id}/cancel/`; creation is the feature's endpoint returning 202 and the job id. | Builds on Celery and `Idempotency-Key`; the web `useJob` feeds the PD-B04 `useOperation`/`OperationStatus` and the realtime hub. First adopter is chosen in T05 from the synchronous long operations found in the census (final archive export, imports, simulation); the rest stay synchronous and are listed. |
| `APPROVAL` (T06) | `ApprovalRequest` (workspace, event, action key, subject reference, payload snapshot and digest, status `pending`, `approved`, `rejected`, `cancelled`, `expired`, `executed`, requested_by, expiry) and `ApprovalDecision` (actor, approve or reject, note; one per actor). An `ApprovalPolicy` registration names who may decide, minimum approvals and whether the requester may approve (default no). A gated operation calls `require_approval`: a matching approved request (same digest) is consumed once, otherwise 409 `approval_required` with the request id. | Approval only gates an operation whose effect is unchanged; it never computes scores, winners, permissions or deadlines. Gates are **off by default** and enabled per event through the `eventconfig` registry, so existing behavior does not change. All transitions are audited; expiry is enforced on read and act plus a beat sweep. | One existing high-impact operation adopts it in T06 (chosen there, off by default). `EligibilityReview` and `TemporalGate` keep their own semantics. |
| `THREADS` (T07) | `Thread` (event, subject reference, audience) and `ThreadComment` (author, plain-text body up to 4,000 characters, one level of replies, mentions, edited, tombstoned when removed). `audience` is a closed enum (`organizers`, `judges`, `participants`, `project_team`, `public`) resolved by a registered per-subject function. | Who may read or post is computed by the registered resolver on the server, never by the client. A mention is only accepted for a user who can read the thread (no leak by mention), and notifies through the existing inbox service. Removal is a tombstone by the author or an organizer, audited. | The four existing note/comment models are **not** migrated or dual-written in this batch (different semantics: public moderated comments, room-private notes, mentor notes, broadcasts); new features must use THREADS instead of adding a new `*Note` model. First adopter in T07: internal organizer notes on applications and projects. |
| `TIMELINE` (T08) | Derived, not stored. Providers register `TimelineItem(kind, key, label, starts_at, ends_at, source, editable, write)` from event dates, registration and submission windows (`TemporalGate`), `AgendaSession`, `PublicationSchedule`, stage data and reminders. `GET .../events/{e}/timeline/?from&to&kinds` returns items in order with instants plus the event time zone and deterministic `conflicts` (overlap in one location or track, a window that closes before it opens, publication before judging ends, items outside the event window). | Conflicts are advisory facts, never blocks; changing a time goes through the existing domain write each item names (as in the configuration registry), with its own validation and audit. | Reuses the `eventconfig` write descriptors and readiness `Reason` shape. Adopters: the organizer overview's upcoming list and an organizer timeline view. |

**QUERY as built (T01).** `core/entities.py` (registry and field types), `core/query.py` (validate, compile, run), `core/entity_views.py` (catalogue and page endpoints), entity registrations in `events/entities.py` and `projects/entities.py`; developer guide `docs/api/ENTITY_QUERY.md`. Refusals are 400 bodies keyed by the path of the offending part (`filter.and[1].op`); a date without a time means the start of that day in UTC; the response carries `total`, `limit`, `offset` in the body (not headers, unlike `core.pagination`). The web side is `lib/entityQuery.ts` and `FilterBuilder`. Two independent domains (events, projects) register entities, and one registry conformance test proves every registered field filters and sorts.

**SAVED_VIEWS as built (T02), with one correction to the table above.** `core.SavedView` (migration `core.0002`), `core/saved_views.py` and `saved_view_views.py`, web `lib/savedViews.ts` and `ViewBar`; guide `docs/api/SAVED_VIEWS.md`. The table said the URL form is `?view=<id>` **or an inline `?filter=`**; the inline form is dropped: filters can hold free text and personal data, and the URL-state rules (PD-B04, `lib/urlState.ts`) forbid that in URLs. The shareable URL carries the view id only, in one `view_<entity>` param per entity (a page can hold several lists; one shared `view` param made each list drop the others' views). Saving validates the definition; updates carry a `version` (409 on a stale one); audits never copy filter values; a view that no longer fits is 409 `view_outdated`; views are per-user working state and excluded from the event archive with that reason.

**DATA_GRID as built (T03).** `components/DataGrid.tsx` (controlled, server-driven table) and `components/EntityGrid.tsx` (catalogue, filter builder, saved views, column picker, sort select, density, paging); guide `docs/operations/DATA_GRID.md`. Adopters: the applications list (Participants > Registration, replacing a hand-written list, with the approve, waitlist and reject actions as row actions) and a new Projects list (Participants > Projects). Correction to the table: row keyboard navigation is on the row checkboxes (native table semantics kept, not the ARIA grid role), and on narrow screens rows stack as cards so sorting moves to the **Sort by** select. Default columns of the applications entity are the ones the old list showed; decided by and decided at are optional columns.

**BULK_PLAN as built (T04).** `communications/bulk.py` keeps its planner, token format and endpoint; it gains `BulkAction` and `register_action` (the five built-ins are registered through it; other apps add `params`-based actions), receipt list and detail endpoints, and the web `lib/bulk.ts` and `BulkPlanner` (preview, exact effects, apply, receipt, stale and retry handling) on a shared `Modal`, which `ConsequenceDialog` now also uses. Adopter: move projects to a track from the Projects grid. Rollback is whole-batch and automatic; compensation after apply stays a deliberate inverse operation (documented in `docs/api/BULK_OPERATIONS.md`). Not built: a bulk history screen (the receipts are API-only) and bulk actions other than the track move in the web.

**ASYNC_JOB as built (T05).** `core/jobs.py` (kinds registry, `enqueue`, `run`, `cancel`, `sweep`, `describe`), models `Job`, `JobLog` and `JobArtifact` (migration `core/0003_jobs`), Celery tasks `core.tasks.run_job` and `sweep_jobs` (beat, 60 s), endpoints `GET jobs/`, `GET jobs/{id}/`, `POST jobs/{id}/cancel/` and `GET jobs/{id}/artifacts/{name}/`, and the web `lib/jobs.ts` (`followJob` feeds `useOperation`) with the Operations > Exports and jobs panel. Guide: `docs/operations/JOBS.md`. Adopter: the event archive export (`POST .../archive/export-jobs/`; the synchronous `GET .../archive/` is unchanged). Correction to the table: artifacts are stored in the database (bounded, 25 MB) because the object-store adapter has no generated-file path yet; the web follows by polling, not the realtime hub. Stays synchronous and listed: archive import and preview, the event simulator and judge-assignment dropout simulation (request-bound, answered to the caller). Not built: retention, automatic retry, push updates.

**APPROVAL as built (T06).** `core/approvals.py` (policies registry, `require_approval`, `dry_run`, `decide`, `cancel`, `sweep`, `describe`), models `ApprovalGate`, `ApprovalRequest` and `ApprovalDecision` (migration `core/0004_approvals`), endpoints under `events/{e}/approvals/` and `approval-gates/`, and the web `lib/approvals.ts` with the Operations > Approvals panel. Guide: `docs/operations/APPROVALS.md`. Adopter: sending a message to an audience (single endpoint and the bulk planner's `send`), off by default, switched by the setting `approvals.message_send`. Correction to the table: the request stores a `summary` (what approvers read) and the `digest` of the full payload rather than a payload snapshot, because a bulk payload can be large; the digest still binds the approval to the content. Not built: deciders are not notified (they open the panel), no delegation or thresholds, other bulk actions are not gated.

**THREADS as built (T07).** `core/threads.py` (subject registry with one rule per audience, post, edit, remove, view), models `Thread` and `ThreadComment` (migration `core/0005_threads`), endpoints `GET/POST events/{e}/threads/{subject}/{id}/{audience}/` and `PATCH/DELETE events/{e}/thread-comments/{id}/`, mention notices through the inbox (`communications/threads.py`), and the web `ThreadPanel`, `NotesDialog` and `lib/threads.ts`. Guide: `docs/operations/THREADS.md`. Adopters: internal organizer notes on applications and projects ("Notes" in the Registration and Projects grids). Corrections to the table: mentions are `@username` text resolved on the server (no user picker), the `public` audience is a rule for workspace members until a signed-out surface exists, and threads are excluded from the event archive. `Modal` now closes on Escape wherever focus is. Not built: note counts in the grids, attachments, reactions, edit history.

**TIMELINE as built (T08).** `core/timeline.py` (provider and rule registries, `build`), `GET events/{e}/timeline/` (`from`, `to`, `kinds`, `limit`), providers for the event dates, gates, publication, agenda, office hours, voting and pending reminders in `eventconfig/timeline.py`, and the web `lib/timeline.ts`, Operations > Timeline and the overview's "Coming up" card. Guide: `docs/operations/TIMELINE.md`. Conflicts are advisory and deterministic (`window_inverted`, `<axis>_overlap`, `outside_event`, `publication_before_voting_closes`); each item names the existing domain write that changes its times (`write`, with `extra` fields where an endpoint needs them) and the page sends changes there. Corrections to the table: no judging window exists, so community voting stands in for "publication before judging ends"; stages carry no times; the old `timezone-timeline` endpoint stays. Not built: public or participant timelines, a calendar grid, drag to reschedule, editing office hours or reminders.

**Surface matrix as closed (T91).** `web` pass: Data grid with saved views on applications and projects, bulk planner dialog, Exports and jobs, Approvals, Notes dialog, Timeline and the overview's Coming up card, each at 390 and 1440 with axe and overflow checks. `api` pass: the generic entity, view, job, approval, gate, thread and timeline endpoints plus bulk receipts, all in the checked OpenAPI. `audit` pass: every stored-state change is audited (`MATRIX.md`). `docs` pass: one guide per primitive, `docs/architecture/SHARED_PRIMITIVES.md`, `docs/operations/UPGRADES.md` and the API index. `sdk` not required, but the TypeScript and Python clients are regenerated and `make sdk-check` is clean, so the web uses them through `apiRequest`. `cli`, `mcp`, `event_as_code`, `webhook`, `archive`, `analytics` and `search` are not required by this batch: the primitives add no verb to the CLI or MCP adapter, no Event-as-Code key (gates are an event setting readable through the configuration registry), no webhook event, no archive table (`core.job`, approvals and threads are excluded as operational or private state), no analytics metric and no search index. Every surface delegates to one operation: the grid, the bulk dialog, the panels and the timeline only call the endpoints above and render the server's answer.

### Forbidden in this batch

A second filter grammar or ad-hoc `query_params` parsing in new list endpoints; a saved-view, job, approval, thread or timeline table per feature; client-side filtering or sorting of server sets; `core` importing domain models; raw SQL or ORM lookup strings accepted from clients; a generic compensation engine claimed without domain inverses; migrating or deleting `SavedPublicSearch`, `BulkReceipt`, `Comment`, `DeliberationNote`, `MentorNote` or `Message`; approvals that decide official outcomes; free-text audiences or client-declared visibility on threads; approval, job or view state kept only in the browser.

### Compatibility and migration boundary

- Additive schema only (`SavedView`, `Job`, `JobLog`, `ApprovalRequest`, `ApprovalDecision`, `Thread`, `ThreadComment`); no backfill; nothing changes for events that never use them.
- Unchanged: every existing endpoint, response shape, bulk token format, the public saved searches, and the four note/comment models.
- New tables are event-scoped where they have an event and are reviewed against `test_every_event_owned_model_is_archived_or_explicitly_excluded` as they land (jobs are operational and excluded from the archive with a recorded reason; saved views, approvals and threads are decided per task).
- Registry status in `PRIMITIVE_REGISTRY.yaml` moves from `PLANNED` to `IMPLEMENTED` only when the owner task is DONE; dependents (F001 configuration filters, F002-B02 editors and explanations) are listed so they adopt rather than rebuild.

### Task boundaries (this batch vs neighbours)

T01 QUERY then T02 SAVED_VIEWS and T03 DATA_GRID, then T04 BULK_PLAN on top of T03 selection; T05 ASYNC_JOB, T06 APPROVAL, T07 THREADS and T08 TIMELINE are independent of each other and run after T04 in that order. **Not here:** schema-driven editors, rich text, file preview, notifications, version diff, policy explanations, provenance and extension manifests (F002-B02); preview-as-role and frozen-version infrastructure (F002-B03); full-text search; dashboards.

### Verification strategy

Per primitive: a registry conformance test (every registered entity, field, kind, policy or provider resolves and is authorized), AST/param fuzz and boundary cases with path-keyed diagnostics, role and tenancy matrices, idempotent replay and concurrent-transition cases (job, approval), the stale-state 409 path, audit rows, and a compatibility test that legacy endpoints are byte-for-byte unchanged. Web: unit tests for each state and keyboard contract, browser specs at 390 and 1440 with axe on the first real adopter of each UI primitive. Gates: `make verify-fast`, `make e2e-fast`.

## PD-F002-B02 canonical contract (2026-10-01)

The queue has no T00 task for this batch, so the contract is written first under PD-F002-B02-T01 (same method as B01-T00). Evidence for statements about current behavior: `docs/verification/PD-F002-B02/T01-census.log` (`probe_census.py`, read-only, run against the live stack). Escalation for the architecture decisions: `docs/execution-v3/escalations/ESC-20260930-005.yaml` (resolved with the conservative default, the same as ESC-20260930-004).

### What exists today (census)

- **Schemas exist twice.** `presentation/block_types.py` declares 12 page blocks with a documented JSON-Schema subset (object, bounded string, bounded integer, bounded array of objects, `x-widget`, `x-nonblank`, `x-create-default`), validated by `normalize_config`/`clean_config` and mirrored on the client by `features/page-builder/configSchema.ts` and `ConfigFields.tsx` (generated catalogue `blockSchemas.generated.ts`). The setting registry (`eventconfig/registry.py`) carries 18 `SettingSpec.schema` descriptors (string, boolean, integer, number, array, nullable) that only the read-only Defaults and overrides panel looks at.
- **Rich content exists twice.** Organizer rich text is an allowlist HTML sanitizer (`presentation/sanitize.py`, 12 tags, `href` only, applied on save and on render); participant project descriptions render CommonMark with `markdown-it` (raw HTML off, images off, tables on, Pygments highlighting, headings demoted) in `presentation/technical.py`. The participant editor is `ProjectStoryEditor.tsx`. There is no preview endpoint, no structured render tree and no shared model.
- **Artifact inspection exists, preview does not.** `artifacts/inspector.py` statically inspects uploads (type by magic bytes, archive listing, secrets, executables, 4,000-character text preview, findings) and serving is attachment-only; nothing presents that as one safe preview contract, and job outputs (T05 of the previous batch) have none.
- **No preferences.** `Message`/`MessageRecipient` deliver to the inbox and best-effort email to everyone in the audience; `UserProfile` has visibility but no notification settings; webhooks are workspace integrations, not personal preferences.
- **Diffs are flat.** `audit.services.snapshot_fields`/`diff_snapshots` produce `{field: {before, after}}` captured in audit metadata; config history restores those values and renders structured values as raw JSON; forms and rubrics keep immutable published versions with restore-to-draft; eight models carry a `version` counter. There is no structural or text diff.
- **Explanations are three shapes.** Policy evaluation returns an allowed flag plus a visited-node trace (`trace_evaluate`), readiness returns items `{id, severity, passed, detail, module, fix}`, deletion consequences return `{allowed, blockers, consequences}` with `{code, message}` entries.
- **Provenance is scattered.** `AuditEvent` records actor, action, target and free metadata; judging stores a provenance snapshot, the final archive a `provenance` section, signed archives a checksum envelope; nothing names the inputs and rules behind a derived or exported result in one shape.
- **Extensions are deployment source.** `docs/architecture/EXTENSION_SDK.md` describes six families (artifact validators, advancement strategies, assignment strategies, page blocks, archive converters, import/export) plus the registries added in B01; nothing declares an id, version or capability, so an operator cannot list what a build provides.

### Shape decisions for all eight primitives

1. **Same placement and direction as B01.** Server code in `src/api/core` (never importing a domain app; domains register from `AppConfig.ready()`), web code in `src/web/lib` and `src/web/components`. Registries of code-owned definitions plus one generic endpoint family; stored state only where it has lifecycle meaning (`NotificationPreference` only; everything else is derived or lives in existing rows such as `AuditEvent.metadata`).
2. **Unify by adoption, not migration.** Each primitive absorbs the existing near-implementation behind the same behavior and adds the missing generic parts. Existing endpoints, stored values, public HTML and the generated block catalogue stay byte-for-byte compatible, proved by conformance tests on the real data (all 12 block schemas, the technical-description fixtures, the config-history entries).
3. **One definition, two languages.** Where server and browser must agree (schema validation, structured content), the contract is a JSON fixture set run by both pytest and vitest, so the two implementations cannot drift.
4. **Untrusted content stays data.** Anything a participant, external system or inspected file supplies is rendered as text or through a closed node set; no raw HTML, no `dangerouslySetInnerHTML`, no active content, no URL scheme beyond http, https and mailto.
5. **Deterministic and reviewable.** Validation, diffs, explanations and manifests are pure functions of their inputs; none of them decides a score, winner, permission or deadline, and none involves a model.
6. **Same error shape as B01**: DRF 400 bodies keyed by the path of the offending part; 404 for what a caller may not see; 409 with a machine `code` for stale state.

### Per-primitive contract

| Primitive (task) | Canonical state and lifecycle | Authority boundary | Reuse and migration |
|---|---|---|---|
| `SCHEMA_EDITOR` (T01) | A schema is the documented JSON-Schema subset: `object`, `string`, `integer`, `number`, `boolean`, `array`, `enum`, nullable as `[T, "null"]`, bounds (`minLength`, `maxLength`, `minimum`, `maximum`, `minItems`, `maxItems`), `default`, `additionalProperties`, and the keys `x-widget` (`input`, `textarea`, `select`, `switch`, `datetime`), `x-nonblank`, `x-create-default`, `x-help`. Stateless. `core/schema.py`: `check(schema)` (is it inside the subset), `validate(schema, value)` returning path-keyed problems, `defaults`, `normalize`. | Schemas are code-owned: a client never supplies one and the server re-validates in the domain endpoint that owns the value. No `$ref`, conditionals or schema authoring by organizers. | Absorbs `normalize_config` and `configSchema.ts` (conformance on all 12 block schemas and on shared fixtures run by pytest and vitest) and exposes `SettingSpec.schema`; new web `SchemaForm`. Adopters: Defaults and overrides becomes editable in place through each setting's documented write, and the page builder renders through the shared form. |
| `RICH_DOC` (T02) | Source text in a registered **profile** (`story`: CommonMark subset, no HTML, no images, tables, highlighted code, headings demoted; `page`: the existing allowlist HTML). `core/rich.py`: `render_html(source, profile)` for server pages and `render_tree(source, profile)` returning a closed node tree (paragraph, heading, list, quote, code, table, text, emphasis, strong, code span, link) that React renders with no HTML injection. Stateless, size-bounded. | Link schemes http, https, mailto and relative; nodes outside the set are dropped, never passed through. A preview endpoint renders for the caller only and stores nothing. | `presentation.technical` and `sanitize` delegate to the profiles with byte-for-byte identical public output (fixture regression). Adopter: the participant story editor gains a preview through the same renderer. |
| `ARTIFACT_PREVIEW` (T03) | A `PreviewDescriptor` derived on read from a registered source: kind (`text`, `image`, `video`, `document`, `archive`, `data`, `link`, `unavailable`), safe facts, findings with levels, bounded text, archive entries, and a reference to the existing attachment download for media. Never stored. | Visibility is the source's own rule (artifact visibility and role checks); a file is never rendered or executed server-side, active content gets `unavailable` with the reason, and secrets are withheld per the artifact rules. | Wraps `artifacts.inspector` and serving; job outputs register a second source. Adopters: artifact review and the job output list. |
| `NOTIFICATIONS` (T04) | `NotificationPreference(user, workspace, category, channel, enabled)`; categories are code-owned definitions (`announcement`, `mention`, `approval`, `job`, `essential`) with a default and whether the person may turn them off (`essential` never). Channels: `inbox` (always kept for non-essential categories so nothing is lost), `email`. | A person only reads and writes their own preferences; delivery code asks `notifications.wants(user, workspace, category, channel)`; an opt-out never removes the inbox copy and never applies to essential or safety notices. | Message email delivery and thread mention notices consult it; no existing delivery changes for people without a stored preference. Adopter: a Notifications section on the profile. |
| `VERSION_DIFF` (T05) | Pure functions: `diff_json(before, after)` returns ordered changes `{path, op, before, after}` with JSON-pointer-like paths; `diff_text(a, b)` returns line hunks; both bounded and deterministic. A `VersionSource` registry (`list`, `snapshot`) lets a versioned resource offer any two of its versions for comparison. | Read-only. Restoring stays the domain's own endpoint (config history, forms, rubrics). | Reads the existing `{field: {before, after}}` audit diffs and form and rubric version snapshots; absorbs the flat diff as the first level. Adopters: Configuration history and form versions render a `DiffView`. |
| `POLICY_EXPLAIN` (T06) | A common `Explanation {outcome (allowed, blocked, needs_action, unknown), summary, reasons[{code, severity, message, facts?, fix?}]}` with builders and adapters for the three existing shapes (policy trace, readiness item, consequence blocker). Derived, never stored. | Explains a decision the domain already made; it never decides. Facts shown respect the caller's visibility (no hidden data in a reason). | Adapters keep each existing endpoint's shape and add the common form beside it. Adopters: the policy debug result and the consequence dialog's blockers. |
| `AUDIT_PROVENANCE` (T07) | A provenance **envelope** `{by, at, source{kind, id}, inputs{digest, refs}, rules{name, version}, summary}` recorded in the existing `AuditEvent.metadata["provenance"]` and attached to job results and exports. No new table; the digest is the SHA-256 of canonical JSON of the inputs. | An envelope states what was used and by whom; it adds no signature layer. A digest is only kept where a downloaded file or result must be checkable later (exports, official outputs). | Reuses `record_mutation` and the archive and signed-archive digests. Adopters: archive export job result and config restore. |
| `EXTENSION_MANIFEST` (T08) | A code-owned `Manifest {id, version, label, api_version, provides[], requires[]}` per deployment source, with capabilities named after the registries (`page_block`, `artifact_validator`, `advancement_strategy`, `bulk_action`, `job_kind`, `approval_policy`, `thread_subject`, `timeline_provider`, `entity`, ...). Derived at startup from the live registries plus declared manifests; checked for unique ids, resolvable requirements and a supported `api_version`. | Read-only listing for admins; no loader, no runtime permission model, no organizer-supplied code. | Describes the six SDK families and the B01 registries uniformly; adopter: an admin Extensions list and a startup conformance check. |

### Forbidden in this batch

A second schema subset or validator in a feature; raw HTML or `dangerouslySetInnerHTML` for participant or external content; a schema, manifest or content profile accepted from a client; rendering, executing or opening a submitted file on the server; an opt-out that removes essential or safety notices or the inbox copy; a notification table per feature; a diff or explanation computed in the browser that the server did not produce; an extra hash or signature layer without an offline-verification need; changing stored values, public HTML or generated block catalogues while absorbing the near-implementations; an extension loader or organizer-uploaded code.

### Compatibility and migration boundary

- One additive table (`NotificationPreference`, `core/0006`); everything else is derived or recorded in existing rows.
- Unchanged and proved by conformance tests: block schema validation results, public rich-text and technical-description HTML, artifact inspection output and attachment serving, audit rows and config-history restore, the three explanation shapes, the extension SDK facade.
- Registry status in `PRIMITIVE_REGISTRY.yaml` moves from `PLANNED` to `IMPLEMENTED` only when the owner task is DONE.

### Task boundaries and order

T01 SCHEMA_EDITOR, T02 RICH_DOC, T03 ARTIFACT_PREVIEW, T04 NOTIFICATIONS, T05 VERSION_DIFF, T06 POLICY_EXPLAIN, T07 AUDIT_PROVENANCE (may embed a T05 diff summary), T08 EXTENSION_MANIFEST last (it lists the registries the others add). **Not here:** preview-as-role and frozen-version infrastructure (PD-F002-B03), a schema authoring UI, a WYSIWYG editor, full-text search, push notifications.

### Verification strategy

Per primitive: a conformance suite against the real near-implementation (differential, on real data), fixtures shared by pytest and vitest where two languages must agree, path-keyed boundary and fuzz cases, role and tenancy matrices, size and depth limits, the untrusted-content cases (script, event handlers, `javascript:` and data URLs, nested and oversized input), audit rows, and a legacy-unchanged test. Web: unit tests for every state and keyboard contract and browser specs at 390 and 1440 with axe on the first adopter of each UI primitive. Gates: `make verify-fast`, `make e2e-fast`.

### B02 as built

**SCHEMA_EDITOR as built (T01).** `core/schema_subset.py` (`check`, `validate`, `normalize`, `defaults`, `api_errors`; named so it does not collide with the API schema class in `core/schema.py`), the browser twin `lib/schema.ts`, and `components/SchemaForm.tsx`; guide `docs/architecture/SCHEMA_SUBSET.md`. Conformance: 42 shared fixtures run by pytest and vitest, and a differential test of `normalize_config` against a frozen copy of its previous implementation over generated values on all 12 block schemas (it caught one message difference, which was fixed, so output is byte-identical). Adopters: the page builder (`ConfigFields` renders through `SchemaForm`, validation through `lib/schema.ts`) and Setup > Defaults & overrides, which now edits every editable setting in place through the write descriptor each setting names. Corrections to the table: schemas may omit bounds (the registry's descriptors do) and then get platform caps; `format: date-time` and `uniqueItems` joined the subset because registry settings use them.

**RICH_DOC as built (T02).** `core/rich.py` (profiles `story` and `page`; `render_html`, `render_tree`, `RichError`), the sanitizer moved unchanged to `core/rich_page.py`, `POST /workspaces/{id}/rich/preview/`, web `lib/rich.ts`, `RichDoc` (draws the server's tree) and `RichEditor` (text box and preview); guide `docs/operations/RICH_CONTENT.md`. Conformance: 22 shared fixtures (server trees checked by pytest, drawn and checked by vitest) and a differential test of the `story` profile against a frozen copy of the old renderer over 300 generated documents. Adopters: `presentation.technical` and `presentation.sanitize` (delegate) and the participant project story editor, which gains the preview. Deviations from the table: the preview endpoint is workspace scoped, not event scoped (it needs no event data); `link` allows only http, https, mailto and relative URLs in the HTML rendering too, so stories no longer link `ftp:`, `tel:` or `git:` (the one intended difference, tested), and the node set gained `rule`, `break`, `item`, `row` and `cell` to hold lists, tables and thematic breaks.

**ARTIFACT_PREVIEW as built (T03).** `core/previews.py` (sources, `Subject`, the pure `descriptor`), `GET /workspaces/{id}/previews/{source}/`, `artifacts/previews.py` (sources `project_artifact` and `job_output`), `artifacts/access.py` (the reviewer visibility rules, now shared by the review views and the preview) and `core.jobs.visible_to`; web `lib/preview.ts`, `ArtifactPreview` and `PreviewLoader`; guide `docs/operations/ARTIFACT_PREVIEW.md`. Conformance: the real inspector over twelve kinds of content, a role matrix for both sources and a source registered by an independent consumer. Adopters: the reviewer artifact inspector (its findings, facts and excerpt now come from the descriptor) and a Preview button per output in Exports and jobs. Deviations from the table: one endpoint takes each source's own query parameters instead of a path per source; the descriptor gains `detected_type`, `findings_total`, `entries_total` and `inspected_at`; the kind `video` and `document` have no inline player or viewer (the platform never renders a submitted file), so they show facts, findings and the existing download.

