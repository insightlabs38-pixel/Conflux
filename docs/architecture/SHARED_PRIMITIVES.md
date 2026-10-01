# Shared primitives

Seventeen platform primitives that features build on instead of adding bespoke screens, tables and endpoints: eight in PD-F002-B01, eight in PD-F002-B02 and one in PD-F002-B03 (below). Each is a registry plus, where it has one, a generic endpoint family, lives in the `core` app (web code in `src/web/lib` and `src/web/components`), and has one guide.

| Primitive   | What a feature registers                                                 | Stored state                                          | Guide                                        |
| ----------- | ------------------------------------------------------------------------ | ----------------------------------------------------- | -------------------------------------------- |
| QUERY       | an `Entity` (fields, types, roles, base queryset) in `<app>/entities.py` | none                                                  | [ENTITY_QUERY](../api/ENTITY_QUERY.md)       |
| SAVED_VIEWS | nothing: a view is a query definition per entity                         | `SavedView`                                           | [SAVED_VIEWS](../api/SAVED_VIEWS.md)         |
| DATA_GRID   | per-row actions and cell renderers on `EntityGrid`                       | none                                                  | [DATA_GRID](../operations/DATA_GRID.md)      |
| BULK_PLAN   | a `BulkAction` (`bulk.register_action`)                                  | `BulkReceipt`                                         | [BULK_OPERATIONS](../api/BULK_OPERATIONS.md) |
| ASYNC_JOB   | a `JobKind` (`jobs.register_kind`)                                       | `Job`, `JobLog`, `JobArtifact`                        | [JOBS](../operations/JOBS.md)                |
| APPROVAL    | an `ApprovalPolicy` and one `require_approval` call                      | `ApprovalGate`, `ApprovalRequest`, `ApprovalDecision` | [APPROVALS](../operations/APPROVALS.md)      |
| THREADS     | a `ThreadSubject` with one rule per audience                             | `Thread`, `ThreadComment`                             | [THREADS](../operations/THREADS.md)          |
| TIMELINE    | a `Provider` (and optionally a conflict rule)                            | none                                                  | [TIMELINE](../operations/TIMELINE.md)        |

## The second batch (PD-F002-B02)

These are mostly stateless: they validate, render, compare, explain and describe, and the server stays the only authority.

| Primitive                     | What a feature registers or calls                                                                                         | Stored state             | Guide                                                 |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------ | ----------------------------------------------------- |
| SCHEMA_EDITOR                 | a bounded JSON Schema in the supported subset; the browser draws it with `SchemaForm`                                     | none                     | [SCHEMA_SUBSET](SCHEMA_SUBSET.md)                     |
| RICH_DOC                      | a content profile (`core.rich`); text is rendered by the server to a closed node tree                                     | none                     | [RICH_CONTENT](../operations/RICH_CONTENT.md)         |
| ARTIFACT_PREVIEW              | a preview source (`previews.register_source`) returning a bounded descriptor                                              | none                     | [ARTIFACT_PREVIEW](../operations/ARTIFACT_PREVIEW.md) |
| NOTIFICATIONS                 | a category (`notifications.register_category`) and one `wants()` call at delivery                                         | `NotificationPreference` | [NOTIFICATIONS](../operations/NOTIFICATIONS.md)       |
| VERSION_DIFF                  | a version source (`version_diff.register_source`) listing and loading versions                                            | none                     | [VERSION_DIFF](../operations/VERSION_DIFF.md)         |
| POLICY_EXPLAIN                | an adapter building an `explanation` from a decision, never deciding                                                      | none                     | [EXPLANATIONS](../operations/EXPLANATIONS.md)         |
| AUDIT_PROVENANCE              | `provenance.envelope` and `attach` on a job result or audit row                                                           | none (in existing rows)  | [PROVENANCE](../operations/PROVENANCE.md)             |
| EXTENSION_MANIFEST            | a `<app>/manifest.py` declaring what the app provides and needs, imported from `ready()`                                  | none                     | [EXTENSIONS](../operations/EXTENSIONS.md)             |
| PREVIEW_CONTEXT (PD-F002-B03) | a `Surface` (`preview_context.register_surface`): the roles it can be viewed as, an optional version source and `resolve` | none                     | [PREVIEW_CONTEXT](../operations/PREVIEW_CONTEXT.md)   |

A new registry in this family is also a **capability** of the extension manifest (`manifest.register_capability`), so adding one entry means adding it to its app's manifest; `manage.py check` fails until the two agree.

## Rules that make them compound

1. **Dependency direction.** A domain registers with `core`; `core` never imports a domain app (only the platform apps `accounts`, `audit`, `workspaces`). `core` reaches the event through `apps.get_model` (see `core.entity_views._EntityView`). A test pins this (`test_core_depends_on_no_domain_app`).
2. **Register in `AppConfig.ready()`** (see `communications/apps.py`, `events/apps.py`, `eventconfig/apps.py`) so the web process and the Celery worker both know the registration. A registry key may be registered once; the identical registration again is harmless, a different one is an error.
3. **Authorization is decided once, in the registration**, and enforced on the server: roles for entities, jobs and approvals, per-audience rules for threads, organizer roles for the timeline. Anything a caller may not see is 404, not 403.
4. **Mutations are audited** (`record_mutation` in the same transaction) and state machines move forward only, under `select_for_update(of=("self",))` (a static test enforces `of`).
5. **Stored state only where it has lifecycle meaning.** Query results and the timeline are derived; jobs, approvals, threads and saved views are stored.
6. **Additive migrations only** (`core/0002` to `core/0006`). No existing table or response changed shape; the older near-primitives (`SavedPublicSearch`, the four note and comment models, the synchronous archive export) stay.
7. **Off by default where behavior could change.** Approval gates are opt-in per event through the setting registry.
8. **No second source of truth.** The web renders what the server returns and never filters, sorts, orders or decides a set itself.

## Adding a consumer: checklist

- Register in `<app>/<primitive>.py`, imported from `ready()`.
- Add the real adopter surface (a grid action, a panel) rather than a demo.
- Tests: a happy path on realistic rows, the refusal cases, who may and may not see it, the lifecycle edge, and (for shared state) a race on PostgreSQL (`tests/integration/concurrency`).
- New event-owned model? Classify it in `EXCLUDED_EVENT_MODELS` (`test_final_archive.py`) or the archive tables. New writable setting? Add its proof to `test_event_overrides.py`.
- A new preview surface or extension entry is declared in the app's `manifest.py` (`manage.py check` fails until it agrees with the registry); a preview reuses the domain's own visibility function and never reads a context outside `core.preview_context`.
- Regenerate the contract: `manage.py spectacular --validate --fail-on-warn --file docs/api/openapi.yaml`, `scripts/generate_sdks.py`, then `make sdk-check`.
- A browser spec (isolated fixture) at 390 and 1440 with axe and an overflow check, listed in `tests/e2e/tiers.json`, `weights.json` and `affected.json`.

The batches' verification matrices are `docs/verification/PD-F002-B01/MATRIX.md` and `docs/verification/PD-F002-B02/MATRIX.md`; the binding contract is spec 002 (`docs/product-depth-v3/specs/002-...md`).
