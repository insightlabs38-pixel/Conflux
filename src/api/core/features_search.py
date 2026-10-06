"""Verifier for the `search` property (PD-F003-B01-T08): how a feature is searched and filtered.

The platform has one query engine (`core.entities` and `core.query`): a domain registers what may
be listed, filtered and sorted about its rows, and the engine compiles a client's query against
that registration and nothing else. A feature either is such an entity or says why it is not, and
a claim is held to the registry:

- `entity:<key>`: the entity is registered, and `fields:<a,b,c>` lists exactly the keys of its
  registered fields, so adding or removing a searchable field without updating the claim fails.
  Each field's column path must resolve from the feature's model through forward relations, and
  the entity's roles must be within the roles that may read the feature under `authorization`, so
  a search cannot reach what the routes refuse. The engine only ever queries the rows `base`
  returns for one event, so a filter on a column with no index of its own (derived from the
  model's `db_index`, unique, foreign key, `Meta.indexes` and constraints) scans one event's rows;
  that holds only when the model reaches `events.Event` through foreign keys, and a filterable
  column that has neither an index nor an event to narrow by is refused.
- `no_query@<reason>`: the feature is read whole through its routes (a short, bounded list) and
  says why a query over it is not offered.
- `test:<path>::<name>`: the proof for an entity (CI checks it exists).

The report lists each field with its type, whether it filters and sorts and whether the column is
indexed, all read from the registry and the model.
"""

from django.core.exceptions import FieldDoesNotExist

from . import entities as registry
from . import features
from .features import problem

MIN_REASON = 20


def parse(claim):
    got = {"entity": [], "fields": []}
    reasons, other = {}, []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        head, _, reason = ref.partition("@")
        if kind in ("entity", "fields"):
            got[kind].append(rest)
        elif head == "no_query":
            reasons["no_query"] = reason
        else:
            other.append(ref)
    return got, reasons, other


def resolve(model, path):
    """The model field a registered column path ends on (forward relations only), or None."""
    current, field = model, None
    for part in path.split("__"):
        try:
            field = current._meta.get_field(part)
        except FieldDoesNotExist:
            return None
        if not getattr(field, "concrete", False) and not getattr(field, "many_to_one", False):
            return None
        related = getattr(field, "related_model", None)
        if part != path.split("__")[-1]:
            if related is None:
                return None
            current = related
    return field


def indexed(field) -> bool:
    """Whether the database can find rows by this column without a scan."""
    if field.primary_key or field.unique or getattr(field, "db_index", False):
        return True
    if getattr(field, "remote_field", None) is not None:  # a foreign key carries an index
        return True
    model = field.model
    for index in model._meta.indexes:
        if index.fields and index.fields[0].lstrip("-") == field.name:
            return True
    for constraint in model._meta.constraints:
        fields = getattr(constraint, "fields", ())
        if fields and fields[0] == field.name:
            return True
    return any(group and group[0] == field.name for group in model._meta.unique_together)


def entity_fields(model, entity) -> list[dict]:
    rows = []
    for item in entity.fields:
        target = resolve(model, item.column)
        rows.append(
            {
                "key": item.key,
                "type": item.type,
                "filterable": item.filterable,
                "sortable": item.sortable,
                "resolved": target is not None,
                "indexed": indexed(target) if target is not None else None,
            }
        )
    return rows


def facts(feature, system) -> dict:
    claim = feature.claims.get("search")
    if claim is None or claim.state != "provided":
        return {}
    got, reasons, _ = parse(claim)
    if "no_query" in reasons:
        return {"query": "not offered", "why": reasons["no_query"]}
    entity = registry.entities().get(got["entity"][0]) if got["entity"] else None
    model = system.model(feature.model)
    if entity is None or model is None:
        return {}
    scoped = system.fk_path(model, "events.Event") is not None

    def describe(f):
        flags = [f["type"]]
        if f["filterable"]:
            flags.append("filter")
        if f["sortable"]:
            flags.append("sort")
        lookup = "indexed" if f["indexed"] else "scan within one event" if scoped else "no index"
        return f"{f['key']} ({', '.join(flags)}, {lookup})"

    return {
        "query": f"entity {entity.key}",
        "roles": sorted(str(r.value if hasattr(r, "value") else r) for r in entity.roles),
        "fields": [describe(f) for f in entity_fields(model, entity)],
    }


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="search"))

    model = system.model(feature.model)
    if model is None:
        return found
    got, reasons, other = parse(claim)
    for ref in other:
        if not ref.startswith("test:"):
            bad("bad_ref", f"'{ref}' is not entity:, fields:, no_query@ or test:.")
    if "no_query" in reasons:
        if got["entity"] or got["fields"]:
            bad("both", "A feature cannot be a query entity and say it is not.")
        if len(reasons["no_query"].strip()) < MIN_REASON:
            bad("no_reason", "Say why a query is not offered (a short sentence).")
        return found
    if len(got["entity"]) != 1:
        bad("entity_ref", "Name one entity (entity:<key>) or say why not (no_query@).")
        return found
    if not any(r.startswith("test:") for r in other):
        bad("no_test", "Name the test that queries the entity (test:).")
    entity = registry.entities().get(got["entity"][0])
    if entity is None:
        bad("entity_missing", f"'{got['entity'][0]}' is not a registered query entity.")
        return found
    declared = sorted(got["fields"][0].split(",")) if len(got["fields"]) == 1 else None
    actual = sorted(f.key for f in entity.fields)
    if declared is None:
        bad("fields_ref", "Declare the entity's fields once (fields:<a,b,c>).")
    elif declared != actual:
        bad(
            "fields_mismatch",
            f"The claim lists {', '.join(declared)} but the entity registers {', '.join(actual)}.",
        )
    rows = entity_fields(model, entity)
    scoped = system.fk_path(model, "events.Event") is not None
    for row in rows:
        if not row["resolved"]:
            bad("column_unresolved", f"The column of '{row['key']}' does not resolve on the model.")
        elif row["filterable"] and not row["indexed"] and not scoped:
            bad(
                "unindexed_filter",
                f"'{row['key']}' can be filtered on, its column has no index and the model has no "
                "event to narrow the scan by.",
            )
    auth = feature.claims.get("authorization")
    if auth is not None and auth.state == "provided":
        allowed = {r.partition(":")[2] for r in auth.refs if r.startswith("readers:")}
        if allowed:
            from .features_authorization import ALL_ROLES

            readers = ALL_ROLES if allowed == {"members"} else set(",".join(allowed).split(","))
            roles = {str(r.value if hasattr(r, "value") else r) for r in entity.roles}
            if not roles <= readers:
                bad(
                    "roles_wider",
                    f"The entity lets {', '.join(sorted(roles - readers))} query what the routes "
                    "do not let them read.",
                )
    return found


def static(feature, claim, root) -> list[dict]:
    """CI: the proving test exists."""
    return features.static_test_refs(feature, claim, root, "search")


features.register_verifier("search", verify, facts=facts, static=static)
