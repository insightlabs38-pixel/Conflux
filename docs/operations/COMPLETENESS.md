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
- `own:<rule>` (`project_member`, `team_member`, `self`): required exactly when roles other than organizers and admins may write, and refused when only they do;
- `test:<path>::<name>`: adversarial tests (checked in CI by `check_static`).

The page shows the derived readers, writers, the scope chain and an Explanation (`core.explain`) in words. Codes: `bad_ref`, `no_routes`, `scope_ref`, `readers_ref`, `writers_ref`, `no_test`, `route_missing`, `route_tenant`, `route_scope`, `route_unmatrixed`, `route_open`, `access_unknown`, `scope_path`, `readers_mismatch`, `writers_mismatch`, `own_missing`, `own_unused`, `own_ref`; CI: `test_file`, `test_name`.

`tests/integration/test_feature_authorization.py` sends the requests: every claimed route and method is refused for each role the matrix excludes, for a signed-in stranger and for a signed-out caller; a workspace member who is not on a project cannot change it, its submissions or its artifacts; and records of another workspace or event are not found. It found one ordering gap, fixed here: the upload-intent endpoint validated the body before resolving the project, so a non-member got a 400 instead of the project's 404.

## Audit events (T04)

The platform records a change by writing an `AuditEvent` in the same transaction as the change (`audit.services.record_mutation`); the action is a literal `subject.verb` in the code. `features_audit.verify` holds an `audit` claim to that code:

- `write:<route>:<METHOD>=<action>`: the route exists and accepts that writing method (the permission matrix lists it); the action follows `subject.verb` and is one the code records (`System.audit_actions` reads the source: an `action=` literal, a conditional's branches or a name assigned one, in a module that calls `record_mutation`); and it is recorded by the app that owns the feature's model or the route's view, so a claim cannot borrow another feature's action;
- completeness is derived: when the feature claims its routes under `authorization`, every writing method of those routes needs a `write:` ref, so a new writing route fails until it is audited;
- `test:<path>::<name>`: the proof, checked in CI to exist.

The proof is `tests/integration/test_feature_audit.py`. It reads the claims, sends each claimed change through the API as the role that may make it and checks the audit row: the declared action, the workspace, the actor, a target, and no secret or token in the metadata. A scenario must exist for every claim and for nothing else. It also proves that a refused change (a stranger, an invalid body) leaves no audit row, that deciding an application twice audits once, that the row and the change roll back together, and that an invite token never reaches the log. Codes: `bad_ref`, `no_test`, `no_writes`, `write_twice`, `route_missing`, `method_unknown`, `action_format`, `action_missing`, `action_elsewhere`, `write_unaudited`; CI: `test_file`, `test_name`.

The harness found real gaps, fixed here with an audit row inside the change's own transaction (metadata names fields and ids, never content, object keys, signed URLs or tokens): `project.created` and `project.updated`; `form.created` and `form.draft_saved`; `evaluation_plan.updated` and `evaluation_plan.deleted`; `artifact.added`, `artifact.upload_started`, `artifact.uploaded` and `artifact.validated`; `submission.draft_saved`; `application.decided` (an approval grants workspace membership and was not recorded); and `team.created`, `team.member_joined`, `team.member_left`, `team.captain_transferred`, `team.invite_created`, `team.invite_revoked` and `team.invite_redeemed`.

## Idempotency and concurrency (T05)

Every change a feature accepts declares what sending it twice does (a retry after a timeout, a double click, two callers at once). `features_idempotency.verify` holds each `mode:<route>:<METHOD>=<mode>` ref to the system:

- `natural`: it sets a state or moves a state machine forward, so repeating it leaves the same state (a second delete finds nothing, a second finalize returns the version it made);
- `unique@<app.Model>.<constraint>`: a duplicate is refused by a uniqueness constraint the model really has;
- `token@<app.Model>.<field>`: a single-use token (a unique field) authorizes the change;
- `locked@<app.Model>.<field>` or `locked@<dotted function>`: a version or revision field refuses a stale write, or the function's code takes a row lock (`select_for_update`);
- `keyed`: the view takes an `Idempotency-Key` (`core.idempotency.IdempotentMixin` is among its bases): the same key returns the first response and runs once, a key reused with a different body is refused (422), keys belong to their caller, and a failed change does not keep its key;
- `none@<reason>`: nothing protects it and a repeat repeats it; the reason (a sentence) says why that is accepted.

Completeness is derived like audit: every writing method of every route claimed under `authorization` needs a mode. Codes: `bad_ref`, `no_test`, `no_modes`, `mode_twice`, `route_missing`, `method_unknown`, `mode_unknown`, `mode_detail`, `unique_missing`, `token_missing`, `lock_missing`, `not_keyed`, `no_reason`, `mode_missing`; CI: `test_file`, `test_name`.

`tests/integration/test_feature_idempotency.py` sends each of the 45 claimed changes twice as the role that makes it and compares what the second send did with the mode: `none` and `keyed` (without a key) repeat the change, every other mode does not (it returns the same state or a refusal, never a server error). It also proves the keyed behavior and that an unkeyed retry of an unprotected change is the documented repeat. Scenarios are the audit proof's, so one request set backs both properties.

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

## The report

`GET /api/v1/workspaces/{id}/completeness/` (organizers and admins; `Cache-Control: private, no-store`; no write method) returns `{properties[], features[], totals, problems[], ok}`. Each feature carries its derived id type and states, its lifecycle graph, its claims and its findings. The page shows findings first (an alert), then a dense features table with identity and a closed lifecycle per row, and the properties not checked yet behind details.

## Initial features

`event`, `track`, `application`, `announcement`, `team`, `project`, `submission`, `stage`, `form`, `artifact`, `evaluation_plan`, `award`, `message`, `webhook`, `policy`. They are listed in the extensions inventory as the capability `feature`, claimed by their app's manifest. More are added by the batches that deepen them.

## Adding a feature or a property

1. A feature: `<app>/features.py` with a `Feature`, imported from the app's `manifest.py`, and `("feature", key)` in its `provides`. `check()` tells you what is missing.
2. A property: its owner task writes a verifier (`register_verifier("rest", verify)`), then claims it for every registered feature (provided with refs, not applicable with a reason, or planned with an owner).

## Boundaries and compatibility

Read-only and stateless: no table, no migration, no audit row, no request depends on it. Not every one of the 122 domain models is a feature, and a model that is not registered is never failed. No endpoint, stored value or route changed for the registry's sake. Escalation: `docs/execution-v3/escalations/ESC-20260930-006.yaml`; contract: spec 003.
