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

## The report

`GET /api/v1/workspaces/{id}/completeness/` (organizers and admins; `Cache-Control: private, no-store`; no write method) returns `{properties[], features[], totals, problems[], ok}`. Each feature carries its derived id type and states, its lifecycle graph, its claims and its findings. The page shows findings first (an alert), then a dense features table with identity and a closed lifecycle per row, and the properties not checked yet behind details.

## Initial features

`event`, `track`, `application`, `announcement`, `team`, `project`, `submission`, `stage`, `form`, `artifact`, `evaluation_plan`, `award`, `message`, `webhook`, `policy`. They are listed in the extensions inventory as the capability `feature`, claimed by their app's manifest. More are added by the batches that deepen them.

## Adding a feature or a property

1. A feature: `<app>/features.py` with a `Feature`, imported from the app's `manifest.py`, and `("feature", key)` in its `provides`. `check()` tells you what is missing.
2. A property: its owner task writes a verifier (`register_verifier("rest", verify)`), then claims it for every registered feature (provided with refs, not applicable with a reason, or planned with an owner).

## Boundaries and compatibility

Read-only and stateless: no table, no migration, no audit row, no request depends on it. Not every one of the 122 domain models is a feature, and a model that is not registered is never failed. No endpoint, stored value or route changed for the registry's sake. Escalation: `docs/execution-v3/escalations/ESC-20260930-006.yaml`; contract: spec 003.
