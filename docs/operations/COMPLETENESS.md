# Feature completeness contract

A deep feature is more than a model and an endpoint. Spec 003 lists 21 properties a feature should consider across every surface; this contract states, in code, which feature provides which, and **checks the claim against the running system**, so completeness is written once, derived where it can be, and cannot drift into a hand-copied table. Code: `core/features.py` (registry, claims, `check()`, `report()`), `core/features_identity.py` (the first verifier), `core/feature_views.py` (report endpoint); each app declares its features in `<app>/features.py` (loaded from its manifest). Web: Operations > Completeness (`lib/completeness.ts`, `features/operations/CompletenessPanel.tsx`).

## The model

```python
from core.features import Feature, Lifecycle, provided, not_applicable, planned, register_feature

register_feature(Feature(
    key="event", label="Event", model="events.Event",
    claims={"identity": provided("field:public_id", "route:event-detail")},
    lifecycle=Lifecycle("choice", field="status", initial=("draft",),
                        transitions="events.views:STATUS_FLOW",      # the code's own table, read not copied
                        terminal=("archived",), via=("events.views.EventStatusView",))))
```

- A **property** is one of the 21 (`identity`, `validation`, `authorization`, `audit`, `idempotency`, `rest`, `sdk`, `search`, then the eight surfaces of PD-F003-B02 and the five platform properties of PD-F003-B03).
- A **claim** is `provided(*refs)` (how: a field, route, registry key, audit action or test), `not_applicable(reason)` or `planned(owner_task)`. A reason is at most 300 characters; a planned owner must exist in `TASKS.yaml` (a test checks).
- A property is **landed** once its owner task registers a **verifier** (`register_verifier`). A landed property must be claimed by every registered feature, a `provided` claim needs a verifier and every ref must resolve; a property that has not landed may be left unclaimed (the page lists those as "not checked yet").
- Facts are **derived**: a lifecycle's states come from the model field's own choices, a transition table can point at the code's own (`"module:NAME"`), the id type and routes come from the model and the URL resolver. Only the claim, its refs, reasons and any graph the code does not hold are declared.
- Advisory at runtime: nothing in a request reads the registry. CI enforces it (`tests/integration/test_feature_contract.py`).

## Identity and lifecycle (T01)

`features_identity.verify` proves, for every feature that claims `identity`:

- the model has a `public_id` that is a **UUID, unique and not editable**; every `route:<name>` in the claim addresses records by a `*_public_id` uuid converter and never by an integer or `pk`;
- a **lifecycle is declared**: `choice` (states are the field's choices), `timestamp` (a nullable time: unset and set), `flag` (a boolean) or `none` with a sentence saying how records change. A `none` lifecycle on a model with a `status`, `state` or `phase` choice field is refused (`lifecycle_hidden`);
- the graph only names real states, starts where the model starts (`initial` equals the field default), every state is **reachable**, terminal states have **no way out**, and what performs the transitions (`via`, a dotted path) exists.

Failure codes: `model_missing`, `id_missing`, `id_type`, `id_unique`, `id_editable`, `id_ref`, `bad_ref`, `route_missing`, `route_id`, `route_sequential`, `lifecycle_missing`, `lifecycle_note`, `lifecycle_kind`, `lifecycle_field`, `lifecycle_states`, `lifecycle_unknown_state`, `lifecycle_initial`, `lifecycle_terminal`, `lifecycle_unreachable`, `lifecycle_via`, `lifecycle_hidden`; and for claims `bad_state`, `no_refs`, `no_reason`, `no_owner`, `reason_too_long`, `no_verifier`, `unknown_property`, `unclaimed`.

## Validation and invariants (T02)

Validation is server-side and keyed: a record the domain refuses is refused with a message naming the part that is wrong. `features_validation.verify` checks a `validation` claim that names **where** it is enforced and **what proves it**:

- `check:<dotted path>`: the function, class or model method that enforces an invariant (must resolve);
- `constraint:<app.Model>.<name>`: a database or model constraint, read from the model's own meta (must exist);
- `test:<path>::<name>`: a test that sends something invalid and sees it refused (the format is checked at runtime and that the file and the test exist is checked in CI by `check_static(root)`);
- at least one of `check:` or `constraint:` and at least one `test:`.

It also **derives** two facts that cannot be declared falsely: an unsaved blank record fails `clean_fields()` with a message per required field (`blank_accepted` if it passes, `blank_error` if it raises something else), and `full_clean()` on a blank record never crashes the model's own `clean()` (`blank_crashes`). The page shows, per feature, the refs, the fields a blank record is refused for, the constraints and whether the model checks its own rules. Codes: `bad_ref`, `check_missing`, `constraint_missing`, `test_ref`, `no_enforcement`, `no_test`, `blank_accepted`, `blank_error`, `blank_crashes`; CI: `test_file`, `test_name`.

The probe found one real gap, fixed here: `Submission.clean()` read unset relations and raised `RelatedObjectDoesNotExist` for a blank record; it now leaves that to field validation, which names every required part (`tests/integration/test_feature_validation.py`). Three features had no refusal test and gained one (track, announcement, message).

## Authorization and scope (T03)

Authorization is decided once, on the server, and the platform already records it: the permission matrix (`core.permission_matrix`) reads the role gates the views really apply. `features_authorization.verify` holds an `authorization` claim to that matrix, so a claim can never say more or less than the code does:

- `route:<url name>` (one or more): each route must exist, carry the workspace in its URL (and the event, for event scope) and appear in the matrix; a route open to anyone signed in or to the public needs an explicit `open:<url name>` acknowledgement;
- `scope:event` or `scope:workspace`: where records live, confirmed by the model's own foreign keys (`System.fk_path` finds the chain to `events.Event` or `workspaces.Workspace`);
- `readers:<roles>` and `writers:<roles>`: who the matrix lets reach the GET routes and the writing routes (`members` for every role, `none`, or a comma list); the claim must equal the matrix, so widening a gate without updating the claim fails;
- `narrow:<route>:<METHOD>=<roles>`: required for every route and method whose roles differ from the stated `readers:` or `writers:` (the claim is the widest group, a narrower route such as a reopen only organizers may do is pinned on its own), so widening one route fails even while another already grants that role; codes `narrow_missing`, `narrow_mismatch`, `narrow_unused`;
- `own:<rule>` (`project_member`, `team_member`, `self`): required exactly when roles other than organizers and admins may write, and refused when only they do;
- `test:<path>::<name>`: adversarial tests (checked in CI by `check_static`).

The page shows the derived readers, writers, the scope chain and an Explanation (`core.explain`) in words. Codes: `bad_ref`, `no_routes`, `scope_ref`, `readers_ref`, `writers_ref`, `no_test`, `route_missing`, `route_tenant`, `route_scope`, `route_unmatrixed`, `route_open`, `access_unknown`, `scope_path`, `readers_mismatch`, `writers_mismatch`, `own_missing`, `own_unused`, `own_ref`; CI: `test_file`, `test_name`.

`tests/integration/test_feature_authorization.py` sends the requests: every claimed route and method is refused for each role the matrix excludes, for a signed-in stranger and for a signed-out caller; a workspace member who is not on a project cannot change it, its submissions or its artifacts; and records of another workspace or event are not found. It found one ordering gap, fixed here: the upload-intent endpoint validated the body before resolving the project, so a non-member got a 400 instead of the project's 404.

## Audit events (T04)

The platform records a change by writing an `AuditEvent` in the same transaction as the change (`audit.services.record_mutation`); the action is a literal `subject.verb` in the code. `features_audit.verify` holds an `audit` claim to that code:

- `write:<route>:<METHOD>=<action>`: the route exists and accepts that writing method (the permission matrix lists it); the action follows `subject.verb` and is one the code records (`System.audit_actions` reads the source, never tests or migrations: an `action=` literal, a conditional's branches or a name assigned one, given to `record_mutation` or to a function that passes its `action` argument on to it); and it is recorded by the app that owns the feature's model or the route's view, so a claim cannot borrow another feature's action;
- completeness is derived: when the feature claims its routes under `authorization`, every writing method of those routes needs a `write:` ref, so a new writing route fails until it is audited;
- `test:<path>::<name>`: the proof, checked in CI to exist.

The proof is `tests/integration/test_feature_audit.py`. It reads the claims, sends each claimed change through the API as the role that may make it and checks the audit row: the declared action, the workspace, the actor, a target, and no secret or token in the metadata. A scenario must exist for every claim and for nothing else. It also proves that a refused change (a stranger, an invalid body) leaves no audit row, that deciding an application twice audits once, that the row and the change roll back together, and that an invite token never reaches the log. Codes: `bad_ref`, `no_test`, `no_writes`, `write_twice`, `route_missing`, `method_unknown`, `action_format`, `action_missing`, `action_elsewhere`, `write_unaudited`; CI: `test_file`, `test_name`.

The harness found real gaps, fixed here with an audit row inside the change's own transaction (metadata names fields and ids, never content, object keys, signed URLs or tokens): `project.created` and `project.updated`; `form.created` and `form.draft_saved`; `evaluation_plan.updated` and `evaluation_plan.deleted`; `artifact.added`, `artifact.upload_started`, `artifact.uploaded` and `artifact.validated`; `submission.draft_saved`; `application.decided` (an approval grants workspace membership and was not recorded); and `team.created`, `team.member_joined`, `team.member_left`, `team.captain_transferred`, `team.invite_created`, `team.invite_revoked` and `team.invite_redeemed`.

## Idempotency and concurrency (T05)

Every change a feature accepts declares what sending it twice does (a retry after a timeout, a double click, two callers at once). `features_idempotency.verify` holds each `mode:<route>:<METHOD>=<mode>` ref to the system:

- `natural`: it sets a state or moves a state machine forward, so repeating it leaves the same state (a second delete finds nothing, a second finalize returns the version it made);
- `unique@<app.Model>.<constraint>`: a duplicate is refused by a uniqueness constraint the model really has;
- `token@<app.Model>.<field>`: a single-use token (a unique field) authorizes the change;
- `locked@<app.Model>.<field>` or `locked@<dotted function>`: a field whose name ends in `version` or `revision` refuses a stale write, or the function calls `select_for_update` (found in its syntax tree, so a comment does not count);
- `keyed`: the view takes an `Idempotency-Key` for that method (`core.idempotency.IdempotentMixin` is among its bases and lists the method): the same key returns the first response and runs once, a key reused with a different body is refused (422), keys belong to the signed-in user, and a server error does not keep its key. The key is considered only after authentication and permissions, so a replay is never served to someone the view would now refuse and a signed-out caller leaves nothing behind; a refusal (4xx) is remembered like any answer, so fix the request and send a new key; keys and their stored answers are forgotten after a day (`core.tasks.sweep_idempotency`, hourly on beat);
- `none@<reason>`: nothing protects it and a repeat repeats it; the reason (a sentence) says why that is accepted.

Completeness is derived like audit: every writing method of every route claimed under `authorization` needs a mode. Codes: `bad_ref`, `no_test`, `no_modes`, `mode_twice`, `route_missing`, `method_unknown`, `mode_unknown`, `mode_detail`, `unique_missing`, `token_missing`, `lock_missing`, `not_keyed`, `no_reason`, `mode_missing`; CI: `test_file`, `test_name`.

`tests/integration/test_feature_idempotency.py` sends each of the 40 claimed changes twice as the role that makes it and compares what the second send did with the mode: `none` and `keyed` (without a key) repeat the change, every other mode does not (it returns the same state or a refusal, never a server error). It also proves the keyed behavior and that an unkeyed retry of an unprotected change is the documented repeat. Scenarios are the audit proof's, so one request set backs both properties.

The retry test found changes that repeated silently: sending a message, posting an announcement, creating a project and adding an external artifact all did their work twice. Those four now take an `Idempotency-Key` (opt-in: a request without the header behaves as before). Three creates stay unprotected on purpose, each with its reason: a webhook subscription (its response carries the signing secret, which a stored response would keep), an upload intent (its signed URL expires) and a team invite (its response carries a bearer token).

## REST representation (T06)

The OpenAPI document the running code produces is what the generated SDKs and the typed web transport are built from, so a feature's REST representation is what that document says. `features_rest.verify` reads it (`System.openapi`, made once) and holds a `rest` claim to it:

- `list:<route>` (one or more): a GET exists and its 200 response is an array or a paged object, never a single record (a list documented as one record gives every generated client the wrong type); `no_list@<reason>` says why a feature has none;
- `detail:<route>`: a GET returning one record with a uuid public id; `no_detail@<reason>` says why a record is read only through its list;
- `paging:offset|cursor|unpaged[@reason]`: must equal what the list's query parameters say (`offset`, `limit`, `page`, `cursor`); an unpaged list says why it stays bounded;
- ids are public ids: every `*_public_id` path parameter of those routes is a uuid;
- every writing method of every route claimed under `authorization` is a documented operation with a success response;
- `test:`: the proof (checked in CI to exist).

Codes: `bad_ref`, `no_test`, `list_ref`, `list_both`, `list_missing`, `list_shape`, `detail_ref`, `detail_both`, `detail_twice`, `detail_missing`, `detail_shape`, `route_missing`, `no_reason`, `id_not_public`, `paging_ref`, `paging_mismatch`, `paging_unused`, `op_missing`, `response_missing`; CI: `test_file`, `test_name`.

`tests/integration/test_feature_rest.py` sends the requests: every claimed list returns an array of exactly what its schema describes (required fields present, no undocumented field, public ids), every claimed detail one record, and every refusal of every claimed route (a stranger, a signed-out caller, an unknown id, an invalid body) is JSON in the shared error shape (`detail`, field messages or a list of messages), never an empty or HTML body.

The verifier and the tests found real defects, fixed here: ten list operations were documented as a single record (announcements, artifacts, evaluation plans, events, forms, policies, projects, stages, team invites, tracks), so the generated SDKs typed them wrongly; the message list took an `offset` that the document did not mention; the award output carried `resources` that the schema omitted; and eleven guard clauses answered 404 with an empty body (projects, artifacts, judging results, the scoreboard), now `NotFound` with the shared `{"detail": "Not found."}`.

## Generated SDK representation (T07)

Both SDKs (`sdks/python`, `sdks/typescript`) are generated from the OpenAPI document of the running code, so a feature's operations are those of the routes it claims under `authorization`, every method the permission matrix lists for them. An `sdk` claim says the feature is generated into both clients (`generated:python`, `generated:typescript`) and names its proof (`test:`); `features_sdk.verify` derives the rest:

- every operation of those routes is in the OpenAPI document with an operation id, unique in the document (the id is what both clients and every typed call use);
- the report lists each operation with the response type the TypeScript client gives it (`Track[]`, `Event`, `null` for no body), derived from the document;
- in CI (`check_static`, which has the source tree), each operation id is in both generated files with the right method, and the TypeScript response type equals the type derived from the document, so a list documented as one record, a renamed schema or a stale SDK fails.

Codes: `bad_ref`, `bad_target`, `target_missing`, `no_test`, `no_operations`, `op_missing`, `op_id`, `op_id_twice`; CI: `sdk_missing`, `python_missing`, `ts_missing`, `ts_types_missing`, `ts_type_mismatch`, `test_file`, `test_name`.

`tests/integration/test_feature_sdk.py` calls every claimed operation through the generated Python client, in process against the real API (the client's `opener` is pointed at the Django test client), as the role that makes it: an array for `T[]`, nothing for `null`, a record whose fields are the schema's, and a refusal as an `ApiError` carrying the shared error shape. It ran with no defect after T06, which had already corrected the list types the generated clients inherited.

## Search, filter and index fields (T08)

The platform has one query engine (`core.entities`, `core.query`): a domain registers what may be listed, filtered and sorted about its rows, and the engine compiles a client's query against that registration and nothing else. A feature either is such an entity or says why not, and `features_search.verify` holds the claim to the registry:

- `entity:<key>` and `fields:<a,b,c>`: the entity is registered and the claim lists exactly its registered field keys, so adding or removing a searchable field without updating the claim fails; each field's column path must resolve from the feature's model through forward relations; the entity's roles must be within the roles that may read the feature under `authorization`, so a search cannot reach what the routes refuse;
- the engine only ever queries the rows `base` returns for one event, so a filter on a column with no index of its own (derived from `db_index`, unique, foreign key, `Meta.indexes` and constraints) scans one event's rows; a filterable column with neither an index nor an event to narrow by is refused (`unindexed_filter`);
- `no_query@<reason>`: the feature is read whole through its routes and says why a query over it is not offered;
- `test:`: the proof for an entity (CI checks it exists).

The page shows each field with its type, filter and sort flags and how the column is looked up. Codes: `bad_ref`, `both`, `no_reason`, `entity_ref`, `entity_missing`, `no_test`, `fields_ref`, `fields_mismatch`, `column_unresolved`, `unindexed_filter`, `roles_wider`; CI: `test_file`, `test_name`.

`tests/integration/test_feature_search.py` asks the engine over HTTP: every entity the platform registers belongs to exactly one claimed feature (a new entity without a claim fails), the catalogue offers exactly the claimed fields to exactly the roles that may read, every claimed field filters and sorts as declared (a field that does not sort is refused), an unclaimed field is refused by name and a query never reaches another event's rows. Two features are entities today (applications, projects); the other thirteen say why a query over them is not offered.

## Base UI (T01)

A feature people work with has a base screen: a component that loads its records from the feature's routes, with a test that renders it. The web source is not part of the running API, so the report shows the claim and the checks that need the source tree run in CI (`check_static`). `features_ui.verify` holds a `ui_base` claim to the code:

- `component:<src/web path>` (one or more): the file exists, and among the non-test sources of its own folder a quoted string holds the last literal segment of a route the feature claims under `authorization` (`tracks/`, `messages/`), so a component cannot be named for a feature it never reads;
- `test:<src/web path>`: the test file exists and mentions one of the components;
- `no_ui@<reason>`: there is no screen yet, and why; a feature whose screen is owed is `planned` with the owning task (announcements, PD-S009-B02-T03).

Codes: `bad_ref`, `both`, `no_reason`, `no_component`, `no_test`, `component_path`, `test_path`, `no_routes`; CI: `component_missing`, `screen_reads_nothing`, `test_missing`, `test_unrelated`. The CI check found that the project test renders the team workspace and not the project screen; the claim now names both.

## The report

`GET /api/v1/workspaces/{id}/completeness/` (organizers and admins; `Cache-Control: private, no-store`; no write method) returns `{properties[], features[], totals, problems[], ok}`. Each feature carries its derived id type and states, its lifecycle graph, its claims and its findings. The page shows findings first (an alert), then a dense features table with identity and a closed lifecycle per row, and the properties not checked yet behind details.

## Initial features

`event`, `track`, `application`, `announcement`, `team`, `project`, `submission`, `stage`, `form`, `artifact`, `evaluation_plan`, `award`, `message`, `webhook`, `policy`. They are listed in the extensions inventory as the capability `feature`, claimed by their app's manifest. More are added by the batches that deepen them.

## Adding a feature or a property

1. A feature: `<app>/features.py` with a `Feature`, imported from the app's `manifest.py`, and `("feature", key)` in its `provides`. `check()` tells you what is missing.
2. A property: its owner task writes a verifier (`register_verifier("rest", verify)`), then claims it for every registered feature (provided with refs, not applicable with a reason, or planned with an owner).

## Boundaries and compatibility

Read-only and stateless: no table, no migration, no audit row, no request depends on it. Not every one of the 122 domain models is a feature, and a model that is not registered is never failed. No endpoint, stored value or route changed for the registry's sake. Escalation: `docs/execution-v3/escalations/ESC-20260930-006.yaml`; contract: spec 003.

## Advanced UI (T02)

Advanced and expert functionality stays behind progressive disclosure and is built from the shared advanced components in `src/web/components` (grids, filter builder, saved views, bulk planner, preview bar, version compare, rich editor, schema form, explanations, provenance), not written again per screen. `features_ui.advanced_verify` holds a `ui_advanced` claim to the code:

- `uses:<Component>@<src/web/features path>` (one or more): the component is one of the shared advanced components and the path is a non-test screen under `src/web/features`; in CI the shared component file exists, the screen imports it, and the screen reads the feature (a quoted last route segment, the key of the feature's query entity, or the feature's own key), so a use cannot be borrowed from another feature's screen;
- `no_advanced@<reason>`: nothing goes beyond the base screen, and why; a feature whose advanced screen is owed is `planned` with the owning task.

Codes: `bad_ref`, `both`, `no_reason`, `no_uses`, `component_unknown`, `screen_path`, `use_twice`; CI: `component_missing`, `screen_missing`, `not_imported`, `screen_reads_nothing`. Seven features name shared components, seven say they have nothing beyond the base screen and announcements are planned for PD-S009-B02-T03.

## Bulk operations (T03)

The platform has one bulk planner (`communications.bulk`): an action is registered once, previewed without writing, applied only with the preview's token, audited and receipted. `features_bulk.verify` holds a `bulk` claim to that registry:

- `action:<key>=<audit action>` (one or more): the key is a registered planner action and no other feature claims it; the audit action is one the code records, written by the feature's app or named for the feature (`project.track_moved` for a project), and, when the handler writes it itself, one of the `action=` literals in the handler's source;
- `test:<path>::<name>`: the proof, a test that previews and applies the action (CI checks it exists);
- `no_bulk@<reason>`: a batch does not fit the feature, and why; a feature whose actions are owed is `planned` with the owning task (registration decisions, PD-S012-B03-T08).

Codes: `bad_ref`, `both`, `no_reason`, `no_action`, `no_test`, `test_ref`, `planner_missing`, `action_unknown`, `action_twice`, `audit_shape`, `audit_unknown`, `audit_foreign`, `audit_not_written`, `action_shared`; CI: `test_file`, `test_name`. `tests/integration/test_feature_bulk.py` proves the registry side: every registered action belongs to exactly one claimed feature (a new action without a claim fails), and the audit actions the claims name are exactly the ones a real preview and apply leaves behind. Five features own the five actions (message, project, stage, policy, evaluation plan), registrations are planned, nine say why a batch does not fit.

## CLI commands (T04)

The CLI (`conflux-admin`, `sdks/python/conflux_sdk/cli.py`) is a thin client of the generated Python SDK. Its one table `COMMANDS` maps each command to the generated operation(s) it calls, and `execute` reads the same table, so it holds no rule of its own and every request still passes the API's authorization, validation and audit. `features_cli` holds a `cli` claim to the table:

- `command:<name>` (one or more, `events list`): the command is in the table, every operation it calls is in the generated Python client and is an operation of the feature's own routes; the claimed commands equal the derived set, so a command added for a feature without a claim fails, and so does a claim of a command the CLI does not have;
- `test:<path>::<name>`: the proof (CI checks it exists);
- `no_cli@<reason>`: the CLI has nothing for the feature, and why; a feature whose commands are owed is `planned` with the owning task.

The SDK is not part of the running API, so the report shows the claim and the table checks run in CI (`check_static`). Codes: `bad_ref`, `both`, `no_reason`, `no_command`, `no_test`, `test_ref`, `command_shape`, `command_twice`, `command_shared`; CI: `table_unreadable`, `command_missing`, `op_not_generated`, `command_foreign`, `command_unclaimed`, `cli_exists`, `test_file`, `test_name`. `tests/integration/test_feature_cli.py` proves the table against the API: each command is claimed by exactly one feature or named in `OUTSIDE` (`whoami`, and `events export`/`import`, which run through the archive routes that PD-F003-B02-T08 claims), and each claimed command sends the request its operation describes. The event feature owns five commands; fourteen features say why the CLI has nothing for them.

## MCP tools (T05)

The MCP adapter (`mcp_adapter.tools.TOOLS`) is a catalogue of tools, each one an existing API route called with the credential's own authority, so authorization, scoping, validation and audit are what the route already enforces. `features_mcp` holds an `mcp` claim to the catalogue, at runtime:

- `tool:<name>` (one or more): the tool is registered, its route is one of the routes the feature claims under `authorization`, the method is in the permission matrix and the path arguments are the route's own; the claimed tools equal the derived set (every tool whose route is the feature's). A write tool must reach a route the feature audits (`write:<route>:<METHOD>=` under `audit`) that is gated by roles;
- `test:<path>::<name>`: the proof (CI checks it exists);
- `no_mcp@<reason>`: no tool reaches the feature, and why; a feature whose tools are owed is `planned` with the owning task.

Codes: `bad_ref`, `both`, `no_reason`, `no_tool`, `no_test`, `test_ref`, `catalogue_missing`, `tool_twice`, `tool_shared`, `tool_unknown`, `tool_foreign`, `method_unknown`, `path_arg`, `write_unaudited`, `write_ungated`, `tool_unclaimed`, `mcp_exists`; CI: `test_file`, `test_name`. `tests/integration/test_feature_mcp.py` proves it through the real endpoint: every tool is claimed by exactly one feature or named in `OUTSIDE` (nine tools over routes no feature claims yet: judging, results, voting, analytics, deadlines, mentoring), and each claimed tool succeeds with a credential limited to its own route and is refused with one limited to another. Stages, projects and announcements own five tools; twelve features say why no tool reaches them.

## Event-as-Code (T06)

Event-as-Code (`integrations.eventascode`, see EVENT_AS_CODE.md) describes an event's configuration as a document. Configuration belongs in it; runtime participant data never does. The module declares `SECTION_MODELS`: each part of the document, the model that owns it and the rows an apply writes. `features_eac` holds an `event_as_code` claim to that table, at runtime:

- `section:<name>` (one or more): the section is declared and its owning model is the feature's own model; the claimed sections equal the derived set (every section the feature's model owns), so a section added for a feature without a claim fails;
- `test:<path>::<name>`: the proof (CI checks it exists);
- `no_eac@<reason>`: the feature is not configuration, and why; a feature whose section is owed is `planned` with the owning task.

Codes: `bad_ref`, `both`, `no_reason`, `no_section`, `no_test`, `test_ref`, `module_missing`, `section_twice`, `section_shared`, `section_unknown`, `section_foreign`, `section_unclaimed`, `eac_exists`; CI: `test_file`, `test_name`. `tests/integration/test_feature_eac.py` proves the table against the code: every section is claimed by exactly one feature or named in `OUTSIDE` (`base_prizes` and `page`, owned by models no feature covers yet), and applying a full document to an empty event changes exactly the tables the sections declare. Seven features own the ten sections they cover (event, track, stage with its transitions, form, policy with its gates and bindings, evaluation plan, award); eight say why they are runtime data.

## Webhooks and the outbox (T07)

A change is audited with `record_mutation(action=...)`; passing `event_type=...` to the same call also writes a pending `DomainEvent` in the same transaction (the outbox), and subscribers receive those events as signed webhooks. A feature's audited changes are the `write:` refs of its `audit` claim, and `features_webhook` requires each of them to be exactly one of:

- `emit:<action>=<event type>`: the code records the action with that event type in the same `record_mutation` call (a helper that hands its `action` and `event_type` on counts, resolved per file), and the type is one a subscription may ask for;
- `silent:<action>@<reason>`: no call of the code records the action with an event type, and why subscribers do not need it;
- `test:<path>::<name>`: the proof (CI checks it exists).

Codes: `bad_ref`, `no_test`, `test_ref`, `action_not_audited`, `type_shape`, `emit_not_recorded`, `no_reason`, `silent_but_emits`, `unclassified`, `classified_twice`; CI: `test_file`, `test_name`. `tests/integration/test_feature_webhook.py` proves every claim through the API: each audited change is sent as the role that may make it and the outbox is read (a claimed event type is written to the workspace, a silent change writes nothing) and a refused change leaves nothing behind. The first version of the source scan resolved helpers by name across files and wrongly marked team and artifact changes as emitting; the real requests caught it and helpers are now resolved per file. Of 40 audited changes, 19 are sent to subscribers and 21 are silent; the silent reasons state what is true today (no event type exists, or the change is private) and are the list of gaps for a later batch to close.

## Archive and import (T08)

An event is archived and restored through one frozen contract (`integrations.final_archive_schema.TABLES`): the tables written, how each is reached from the event and which fields travel. Every event-owned model is classified there or in the archive's exclusion list (`tests/integration/test_final_archive.py`), so an unclassified model already fails; what `features_archive` adds is each feature's own answer, exactly one of:

- `table:<app.model>`: the feature's own model (lowercase label) is a table of the archive, so it is exported with the event and restored into a new one. The report shows how the table is reached, how many fields travel and any field left out;
- `root@<reason>`: the feature is the event itself, which is the thing archived and restored as a new draft event (only `events.Event`);
- `excluded@<reason>`: the model is deliberately not archived, and why; it must not be in `TABLES`;
- `test:<path>::<name>`: the proof (CI checks it exists).

Codes: `bad_ref`, `one_answer`, `no_test`, `test_ref`, `contract_missing`, `no_reason`, `root_foreign`, `archived_but_excluded`, `table_foreign`, `table_unknown`; CI: `test_file`, `test_name`. `tests/integration/test_feature_archive.py` proves the claims: every feature says one thing, each excluded model is on the archive's exclusion list and not in its contract, and each claimed table is exported with its rows and restored into a new event with the same number of rows. Ten features are tables, the event is the root, four are excluded (registrations, announcements, webhook subscriptions, messages). Child tables (memberships, versions, ballots and so on) are not claimed per feature; the archive's own classification test covers them.

## Analytics dimensions (B03-T01)

The platform has one analytics summary (`communications.analytics.compute_analytics`, served at `operations/analytics/`): sections of counts and rates over an event, computed from the domain's own tables and never stored. `features_analytics` holds an `analytics` claim to the module, at runtime:

- `section:<name>`: the section of the summary (a field of `EventAnalyticsResponse`) that counts the feature, and the feature's own model is one the analytics module works on (the model classes it imports), so a feature cannot claim a section it has no part in;
- `measure:<section.key>` (one or more): a number, rate or list in that section the feature owns; no measure is claimed by two features;
- `dimension:<field>=<section.key>` (optional): the summary breaks a measure down by a field of the feature's model, and the breakdown's keys are the field's own choices;
- `test:<path>::<name>`: the proof (CI checks it exists);
- `no_analytics@<reason>`: the summary does not count the feature, and why; a feature whose measures are owed is `planned` with the owning task.

Codes: `bad_ref`, `both`, `no_reason`, `analytics_exists`, `one_section`, `no_measure`, `no_test`, `test_ref`, `summary_missing`, `model_not_counted`, `section_unknown`, `path_shape`, `path_foreign`, `measure_twice`, `measure_shared`, `dimension_field`, `dimension_choices`; CI: `test_file`, `test_name`. `tests/integration/test_feature_analytics.py` proves the claims against a real event: every section of the answer and every model the module counts belongs to a claimed feature or is named in `OUTSIDE_SECTIONS` and `OUTSIDE_MODELS` (voting, memberships, ballots, votes), each claimed measure is in the answer, the breakdown by status has exactly the keys of the field's choices, and the numbers match the rows. Five features are counted (registrations, teams, projects, submissions, evaluation plans) and ten say why not.

## Retention and privacy (B03-T02)

The platform has one subject-export, erasure and retention service (`integrations.privacy`): a person's rows in an event are erased (`_personal`), retained as evidence with a stated reason (`_retained`) or, for private files, purged in two phases (`_private_artifacts`). `features_privacy` reads those buckets from the service's own query builders (query-free) and holds a `privacy` claim to them and to the model, at runtime:

- `erased:<bucket>`, `retained:<bucket>`, `purged:<bucket>`: the bucket is the service's, of that kind, and its model is the feature's own or reaches it by at most two foreign keys; no bucket is claimed by two features and every bucket whose model is the feature's own must be claimed;
- `person:<field>=<fate>[@<reason>]`: one per user column of the feature's model (derived, so a new column cannot be missed): `erased` and `purged` need a bucket of that kind on the model, `retained` and `staff` (an organizer acting in their role) need a reason of at least 20 characters;
- `no_personal_data@<reason>`: the model holds no user column and no bucket;
- `test:<path>::<name>`: the proof (CI checks it exists).

Codes: `bad_ref`, `service_missing`, `both`, `no_reason`, `personal_exists`, `no_answer`, `no_test`, `test_ref`, `bucket_twice`, `bucket_unknown`, `bucket_kind`, `bucket_foreign`, `bucket_shared`, `bucket_unclaimed`, `person_unclaimed`, `person_unknown`, `person_twice`, `person_fate`, `person_unbacked`; CI: `test_file`, `test_name`. `tests/integration/test_feature_privacy.py` proves the claims on real subjects: every bucket is claimed by one feature or named in `OUTSIDE` (marketplace profiles, saved searches, check-ins, attendance, person labels), the export lists exactly the service's buckets, erasing a person removes the erased buckets and only theirs and keeps the retained evidence (including ballots, assignments, comparisons, appeals, eligibility responses and message receipts built for the purpose), private files are purged, an organizer who only acted in a role leaves what they decided in place, erasing in one event leaves the same person in another, a replayed erasure removes nothing more, and the report names buckets and fates, never a person. Eight features say what becomes of their person data and seven say they hold none.

Known gap, recorded rather than hidden: form answers (`forms.FormAnswer`) can hold personal data and are in no export or erasure bucket yet; the owner is PD-S013-B02-T05 (account export and data-deletion workflow). The `form` claim says so.
