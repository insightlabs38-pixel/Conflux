# PD-F003 — A cross-surface completeness contract

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §3  
**Queue batches:** PD-F003-B01, PD-F003-B02, PD-F003-B03

## Completion interpretation

This specification is the canonical depth contract for §3. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

## Canonical primitive reuse

- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `BULK_PLAN`
- `DATA_GRID`
- `EXTENSION_MANIFEST`
- `POLICY_EXPLAIN`
- `QUERY`
- `RICH_DOC`
- `SCHEMA_EDITOR`
- `TYPED_CLIENT`
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
| `analytics` | required |
| `search` | required |
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

## Batch scope

### PD-F003-B01 — A cross-surface completeness contract — Cross-surface contract: Stable public i… → Cross-surface contract: Search/filter/i…

- Cross-surface contract: Stable public identity and clear lifecycle
- Cross-surface contract: Backend validation and invariants
- Cross-surface contract: Authorization and scope rules
- Cross-surface contract: Audit events
- Cross-surface contract: Idempotency/concurrency semantics
- Cross-surface contract: REST representation
- Cross-surface contract: Generated SDK representation
- Cross-surface contract: Search/filter/index fields

### PD-F003-B02 — A cross-surface completeness contract — Cross-surface contract: Base UI → Cross-surface contract: Archive/import/…

- Cross-surface contract: Base UI
- Cross-surface contract: Advanced UI
- Cross-surface contract: Bulk-operation support
- Cross-surface contract: CLI inspect/action support when useful
- Cross-surface contract: MCP inspect/plan/action support when useful
- Cross-surface contract: Event-as-Code representation if it is configuration, not runtime participant data
- Cross-surface contract: Webhook/outbox events
- Cross-surface contract: Archive/import/export representation

### PD-F003-B03 — A cross-surface completeness contract — Cross-surface contract: Analytics dimen… → Cross-surface contract: Test-fixture/sc…

- Cross-surface contract: Analytics dimensions
- Cross-surface contract: Retention/privacy semantics
- Cross-surface contract: Extension hooks
- Cross-surface contract: Version/migration behavior
- Cross-surface contract: Test-fixture/scenario support

## PD-F003-B01 canonical contract (T00, 2026-10-01)

Evidence for every statement about current behavior: `docs/verification/PD-F003-B01/T00-census.log` (`probe_census.py`, read-only, run against the live stack). Escalation for the architecture decision below: `docs/execution-v3/escalations/ESC-20260930-006.yaml` (resolved with the conservative default A).

### What exists today (census)

- 122 domain models: 112 have a public id, 22 a lifecycle field, 48 an owning event, 6 all three. The ten without a public id are internal (imported fixtures, a search-tag join, a rate-limit row) and never exposed.
- 373 REST routes under `/api/v1/`; 357 are addressed by a public uuid and one by an event-scoped number (`rules/<int:number>/`, a version counter). The permission matrix has 484 entries, none unknown or unrecognized.
- 165 audit actions in code across 80 subjects (`subject.verb`), and 40 outbox event types; so most audited actions do not reach webhooks.
- Idempotency keys appear in five modules (jobs, thread comments, archive export jobs, workspace creation, the idempotency model); most mutations are idempotent by nature (PUT, forward-only state machines) or not at all.
- Two queryable entities (`applications`, `projects`), five bulk actions, one job kind, 14 MCP tools (12 read, 2 write), a CLI for events only, 11 Event-as-Code sections, one retention policy and subject export and erasure.
- The 966 generated TypeScript operations and the Python SDK are checked against the OpenAPI artifact (`make sdk-check`); `TYPED_CLIENT` is `PLANNED` and owned by a later batch, but the typed web transport and generated SDKs already exist (PD-B04).
- Nothing records which feature provides which of the 21 properties of this spec, so completeness cannot be stated, checked or steered.

### Shape decisions

1. **The contract is executable, not a document.** `core/features.py`: a registry of **features**, each claiming every property as `provided`, `not_applicable` or `planned`, plus a **verifier** per property that checks a `provided` claim against the live registries. Documentation is generated from it, never written beside it.
2. **Registry-first, same direction as F002.** Domains register from `<app>/features.py` in `AppConfig.ready()`; `core` imports no domain app and reaches models by label (`apps.get_model`). Features are declared in the app manifests (capability `feature`), so the extension inventory lists them and `manage.py check` agrees.
3. **A claim is honest or it fails.** A `provided` claim names how (`refs`: registry keys, route names, audit actions, test ids); the property's verifier resolves every ref against the live system. `not_applicable` carries a reason; `planned` carries the owner task id, which must exist in `TASKS.yaml`. A property whose verifier does not exist yet cannot be claimed `provided`.
4. **Bounded and additive.** The initial set is fifteen important features, not all 122 models: `event`, `track`, `application`, `announcement`, `team`, `project`, `submission`, `stage`, `form`, `artifact`, `evaluation_plan`, `award`, `message`, `webhook`, `policy`. More are added by the batches that deepen them. No model, endpoint or stored value changes for the registry's sake; a gap a task finds is fixed only inside a property that task owns, otherwise recorded as `planned` with its owner.
5. **Derived, not duplicated.** A lifecycle's states come from the model's own choices; search fields from the entity registration; REST and SDK operations from the OpenAPI artifact; permissions from the permission matrix; audit actions and outbox events from the code. The registry stores only what cannot be derived (the claim, its refs and reasons).
6. **Advisory at runtime, enforced in CI.** The report never gates a request. A test fails when a claim is unverifiable, a landed property is unclaimed for a registered feature, or a `planned` owner does not exist; a ratchet fails when the count of `planned` claims for landed properties grows.

### The 21 properties and who owns them

| Key | Property | Batch task | What a verifier proves |
|---|---|---|---|
| `identity` | Stable public identity and clear lifecycle | B01-T01 | the model has a unique, non-sequential public id used in every route; the declared lifecycle's states equal the model field's choices and its transitions name the service that makes them |
| `validation` | Backend validation and invariants | B01-T02 | the named invariants exist as model or service checks and each has a test that refuses a bad value with a keyed message |
| `authorization` | Authorization and scope rules | B01-T03 | every route of the feature is in the permission matrix with roles (none unknown) and a test shows a participant and an outsider refused |
| `audit` | Audit events | B01-T04 | every mutation of the feature records a named audit action (in code) and the action follows `subject.verb` |
| `idempotency` | Idempotency and concurrency | B01-T05 | each mutation declares its mode (natural, keyed, token, locked, none) and a retry test proves it |
| `rest` | REST representation | B01-T06 | list and detail operations exist in OpenAPI, ids are public ids, lists are paged, errors use the shared shape |
| `sdk` | Generated SDK representation | B01-T07 | every operation of the feature exists in both generated SDKs and the TypeScript types match OpenAPI |
| `search` | Search, filter and index fields | B01-T08 | the feature is a registered `QUERY` entity whose fields are the declared ones, or says why not |
| `ui_base`, `ui_advanced`, `bulk`, `cli`, `mcp`, `event_as_code`, `webhook`, `archive` | the eight surfaces | PD-F003-B02 | added there |
| `analytics`, `privacy`, `extension`, `versioning`, `fixtures` | the five platform properties | PD-F003-B03 | added there |

A property is *landed* once its verifier is registered (by its owner task); before that, a feature may leave it unclaimed.

### Contract

| Item | Decision |
|---|---|
| Claim | `Claim {state, refs[], reason, owner}`; `provided` needs refs; `not_applicable` needs a reason of at most 200 characters; `planned` needs an owner task that exists |
| Feature | `Feature {key, label, model, claims: {property: Claim}, lifecycle?}`; `model` is an app label and name, resolved at check time |
| Verifier | `verify(feature, claim, system) -> [Problem]`; `system` is a read-only snapshot (models, OpenAPI, permission matrix, audit actions, registries); a verifier never writes and never imports a domain app directly |
| Report | `GET /workspaces/{id}/completeness/` for organizers and admins: features by property with state, refs and problems, plus totals; `Cache-Control: private, no-store`; no write method |
| Web | Operations > Completeness: a dense features-by-properties grid with identity and lifecycle visible per feature (T01), problems first, claims closed behind details; no editing |
| Authority | a claim describes the system and never changes it; no runtime behavior reads the registry |
| Audit | the report writes nothing; features and claims change only through source review |
| Extension boundary | a new feature registers from `<app>/features.py` and is declared in the manifest; a new property is a verifier plus an entry in the properties table |
| Migration | none: no table, no endpoint changed; a gap fix inside an owned property follows the F001 and F002 rule of additive behavior with a compatibility test |

### Forbidden in this batch

A second matrix written by hand beside the registry; a `provided` claim without a verifier or with an unresolvable ref; business rules in a surface (CLI, MCP, UI) that the domain service does not own; retrofitting all 122 models or changing stored values or public routes to satisfy a property; making an unregistered feature fail a gate; LLM or heuristic judgement of completeness; a runtime request depending on the registry.

### Compatibility and migration boundary

- No migration. Existing routes, stored data, audit actions and outbox events are unchanged except where a task fixes a recorded gap inside its own property, with a test that the old behavior still holds.
- `PRIMITIVE_REGISTRY.yaml` is not extended: this is a contract over primitives, not a new primitive; it reuses `QUERY`, `AUDIT_PROVENANCE`, `EXTENSION_MANIFEST`, `ASYNC_JOB`, `POLICY_EXPLAIN`, `VERSION_DIFF` and the generated SDKs (`TYPED_CLIENT` is adopted when its batch lands, ESC-20260930-006).

### Task boundaries and order

T01 identity and lifecycle (registry, report endpoint, Operations grid), T02 validation, T03 authorization (uses the permission matrix and explanations), T04 audit (uses the provenance envelope), T05 idempotency and concurrency (long operations are jobs), T06 REST, T07 SDK, T08 search (uses `QUERY` and the schema subset), then T90, T91, T95. **Not here:** the eight surfaces (PD-F003-B02), analytics, privacy, extension hooks, versioning and fixtures (PD-F003-B03), and any new feature capability.

### Verification strategy

Per property: a verifier unit suite on realistic and deliberately broken claims, a differential test of the derived facts against the live system (every one of the fifteen features resolves), a negative test per failure code, the role matrix of the report endpoint, the ratchet, and for the UI a component test and a browser spec at 390 and 1440 with axe. Gates: `make verify-fast`, `make e2e-fast`.

### B01 as built

**Identity and lifecycle as built (T01).** `core/features.py` (`Property` x21, `Claim` with `provided`, `not_applicable`, `planned`; `Lifecycle` of kind `choice`, `timestamp`, `flag` or `none`; `Feature`; `register_feature`, `register_verifier`, `System`, `check`, `report`), `core/features_identity.py` (the verifier), `core/feature_views.py` (`GET /workspaces/{id}/completeness/`), `<app>/features.py` for eleven apps, capability `feature` in the extensions inventory; web `lib/completeness.ts` and Operations > Completeness; guide `docs/operations/COMPLETENESS.md`. All fifteen features verify with no findings: UUID public ids, no sequential route, seven declared state machines (event, application, submission and artifact as choice graphs, announcement and award as timestamps, webhook as a flag) and eight that state why they have none (track, team, project, stage, form, evaluation plan, message, policy), with the event graph read from the code's own `STATUS_FLOW`. Conformance: a failure code for each way a claim can be wrong, an independent feature on a core model, and a differential check that every status-like choice field of the fifteen models is covered. Deviations from the contract table: a `route:` ref is optional because team and message have no id-addressed route; `Lifecycle` gained `terminal` and `via`; the report's `landed` list drives the page's columns so later properties appear without a UI change.

**Validation as built (T02).** `core/features_validation.py` (verifier, derived facts and the CI check), `register_verifier(..., facts=, static=)` so a verifier can add derived facts to the report and checks that need the source tree. All fifteen features claim validation with at least one enforcement point, a constraint where the model has one and a test that proves a refusal; the verifier derives that a blank record is refused with a message per required field and never crashes `clean()`, which found and fixed `Submission.clean()` crashing on unset relations. Three refusal tests were added for features without one (track, announcement, message). The page's columns follow the landed list, so Validation appears with refs and derived facts in a closed details cell. Deviations from the contract table: the test proof is a named existing test rather than one new generic test per feature; `full_clean` is probed without database checks so the report stays query-free.

**Authorization as built (T03).** `core/features_authorization.py` verifies an `authorization` claim against the live permission matrix (`System.permission_matrix`, `System.fk_path`), so the claim states routes, scope, readers, writers and the object-level rule, and cannot differ from the gates the views apply; `features.static_test_refs` is the shared CI check for `test:` refs. All fifteen features claim it (readers, writers and scope derived and shown as an Explanation on the page). `tests/integration/test_feature_authorization.py` proves wrong-role, stranger, signed-out, non-project-member and cross-workspace/event refusals for every claimed route. Found and fixed: `UploadIntentView` validated the body before the project. Accepted residual: the object-level rules (`own:`) are declared and proven by named tests, not derived, because they live in view code the matrix cannot read; each is covered by a refusal test. Deviations from the contract table: the verifier does not execute requests itself (the integration tests do), so the deployed report stays query-free.



**Audit as built (T04).** `core/features_audit.py` verifies an `audit` claim (`write:<route>:<METHOD>=<action>` refs and a proving test) against the permission matrix and `System.audit_actions` (an AST scan of the source for `action=` literals in modules that call `record_mutation`, cached); changes are derived from the feature's `authorization` routes, so a new writing route fails until it is audited. All fifteen features claim it (45 changes). `tests/integration/test_feature_audit.py` sends every claimed change and reads the audit row (action, workspace, actor, target, no secret), plus refusal, rollback, replay and token-leak cases. Gaps found and fixed: project, form, evaluation-plan, artifact, submission-draft, application-decision and team writes were not audited (22 actions added). Accepted residual: the verifier proves that each claimed change records its claimed action, not that the metadata is complete; routes outside a feature's claimed routes are outside the check until the claim names them. Deviations from the contract table: the action list is derived from source rather than a runtime registry, because `record_mutation` is a plain function with no registration step.

**Idempotency as built (T05).** `core/features_idempotency.py` verifies `mode:<route>:<METHOD>=<mode>[@detail]` refs (natural, unique, token, locked, keyed, none) against the models' uniqueness constraints and fields, the code of the named lock function (it must contain `select_for_update`) and the view's `IdempotentMixin`; changes are derived from the authorization routes. `tests/integration/test_feature_idempotency.py` sends each of the 45 changes twice and checks the second send against the declared mode, and proves the keyed behavior. Found and fixed: sending a message, posting an announcement, creating a project and adding an external artifact repeated their effect on a retry; each now takes an `Idempotency-Key` (additive, OpenAPI descriptions regenerated). Unprotected on purpose, with a reason each: webhook subscription, upload intent, team invite. Deviations from the contract table: `unique` is a sixth mode (a constraint refusing the duplicate is neither natural nor keyed); the modes are declared per change and proved by replay, not by a concurrency harness, and `my-team` creation is checked but not locked, so two simultaneous creates by one person could both succeed (recorded as a limitation).

**REST as built (T06).** `core/features_rest.py` verifies `list:`, `detail:`, `no_list@`, `no_detail@` and `paging:` refs against the OpenAPI document of the running code (`System.openapi`, `System.operation`), with list and detail shapes, public-id path parameters, paging derived from query parameters and every writing operation documented; `tests/integration/test_feature_rest.py` proves lists, details and the shared error shape with real responses. Found and fixed: ten lists documented as a single record, an undocumented `offset`, an undocumented `resources` field on awards and eleven empty-bodied 404s; the OpenAPI document and both SDKs were regenerated. Eight features have no record page of their own and say why; lists are unpaged except messages and each says why it stays bounded. Accepted residual: error responses are not enumerated in the OpenAPI document (the shared shape is proved by the tests, not described to SDK users), and unpaged lists are bounded by the domain, not by a limit parameter; neither is changed here. Deviations from the contract table: "lists are paged" is declared per list with a reason when unpaged, because paging every list is a cross-domain rewrite outside this batch.

**Generated SDK as built (T07).** `core/features_sdk.py` derives a feature's operations from its `authorization` routes (every method in the permission matrix), checks each has a unique operation id in the OpenAPI document and lists its TypeScript response type; the CI check (`check_static`) confirms each operation is in both generated files with the right method and that the TypeScript response type equals the one derived from the document. `tests/integration/test_feature_sdk.py` calls all 60 or so operations through the generated Python client against the real API. The claim is the two targets and the proof; no operation ids are copied into the registry. Accepted residual: the TypeScript client is checked by its generated types and the shared generator tests, not by a runtime call (there is no TypeScript runtime in the Python suite); request body types are not compared field by field, only response types. Deviations from the contract table: operations are derived from the claimed routes rather than declared per operation.

**Search as built (T08).** `core/features_search.py` verifies `entity:`, `fields:` and `no_query@` refs against the query-engine registry (`core.entities`) and the models: declared fields equal registered fields, column paths resolve, entity roles stay within the roles that may read the feature, and filterable columns are indexed or narrowed by an event; `tests/integration/test_feature_search.py` queries the engine over HTTP and proves no registered entity is unclaimed. Applications and projects are the two entities; thirteen features say why they are read whole. Accepted residual: an index fact is read from the model's declarations, not from the database catalogue, and the other thirteen features are not yet searchable (offering them is a later domain batch, not a contract property). Deviations from the contract table: the index rule is derived from the event scoping the engine always applies, not declared per field.

