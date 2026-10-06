"""Verifier for the `rest` property (PD-F003-B01-T06): how a feature is represented over REST.

The OpenAPI document the running code produces is what the generated SDKs and the typed web
transport are built from, so a feature's REST representation is what that document says. A
`provided` claim names the feature's collection and item routes and how its list is paged, and the
verifier reads the document and holds the claim to it:

- `list:<route>` (one or more): the collection route has a GET, and its 200 response is an array
  or a paged object (`results`), not a single record (a list documented as one record gives
  every generated client the wrong type). `no_list@<reason>` says why a feature has no collection.
- `detail:<route>`: the item route has a GET returning one record. `no_detail@<reason>` says why a
  record is not read on its own (it is read through its list).
- `paging:<kind>[@<reason>]`: `offset` or `cursor` when the list takes those query parameters,
  `unpaged` otherwise (with the reason the list stays bounded). The claim must equal what the
  OpenAPI parameters say.
- ids are public ids: every `*_public_id` path parameter of those routes is a uuid.
- every writing method of every route claimed under `authorization` is a documented operation with
  a success response.
- `test:<path>::<name>`: the proof that refusals use the shared error shape (a JSON body with
  `detail`, field messages or a list of messages, never an empty or HTML body); CI checks it exists.
"""

from . import features
from .features import problem

KINDS = ("offset", "cursor", "unpaged")
OFFSET_PARAMS = {"offset", "limit", "page", "page_size"}
WRITES = ("POST", "PUT", "PATCH", "DELETE")
MIN_REASON = 20


def parse(claim):
    """(routes and paging by kind, the reasons given, the other refs) of a `rest` claim."""
    got, reasons, other = {}, {}, []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        head, _, reason = ref.partition("@")
        if kind in ("list", "detail"):
            got.setdefault(kind, []).append(rest)
        elif head in ("no_list", "no_detail"):
            reasons[head] = reason
        elif kind == "paging":
            name, _, why = rest.partition("@")
            got.setdefault("paging", []).append(name)
            reasons["paging"] = why
        else:
            other.append(ref)
    return got, reasons, other


def _response_schema(system, op, statuses=("200", "201")):
    for status in statuses:
        content = (op.get("responses", {}).get(status) or {}).get("content", {})
        schema = (content.get("application/json") or {}).get("schema")
        if schema is not None:
            return schema
    return None


def shape(system, op) -> str:
    """`array of X`, `paged X`, `X` or `none`: what the 200 response of the operation is."""
    schema = _response_schema(system, op, ("200",))
    if schema is None:
        return "none"
    name = ""
    if "$ref" in schema:
        name = schema["$ref"].rsplit("/", 1)[-1]
        schema = system.schema(name)
    if schema.get("type") == "array":
        item = schema.get("items", {}).get("$ref", "").rsplit("/", 1)[-1]
        return f"array of {item or 'values'}"
    results = schema.get("properties", {}).get("results", {})
    if results.get("type") == "array":
        return f"paged {results.get('items', {}).get('$ref', '').rsplit('/', 1)[-1] or 'values'}"
    return name or schema.get("type", "value")


def paging_of(op) -> str:
    names = {p["name"] for p in op.get("parameters", []) if p.get("in") == "query"}
    if "cursor" in names:
        return "cursor"
    return "offset" if names & OFFSET_PARAMS else "unpaged"


def _id_params(op):
    return [
        p
        for p in op.get("parameters", [])
        if p.get("in") == "path" and p["name"].endswith("_public_id")
    ]


def facts(feature, system) -> dict:
    claim = feature.claims.get("rest")
    if claim is None or claim.state != "provided":
        return {}
    got, reasons, _ = parse(claim)
    out = {}
    lists = []
    for route in got.get("list", []):
        op = system.operation(route, "GET")
        lists.append(f"GET {route}: {shape(system, op) if op else 'missing'}")
        out["paging"] = paging_of(op) if op else "unknown"
    if lists:
        out["lists"] = lists
    for route in got.get("detail", []):
        op = system.operation(route, "GET")
        out["detail"] = f"GET {route}: {shape(system, op) if op else 'missing'}"
    for key in ("no_list", "no_detail"):
        if key in reasons:
            out[key] = reasons[key]
    return out


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="rest"))

    if system.model(feature.model) is None:
        return found
    got, reasons, other = parse(claim)
    if not any(r.startswith("test:") for r in other):
        bad("no_test", "Name the test that proves refusals use the shared error shape (test:).")
    for ref in other:
        if not ref.startswith("test:"):
            bad(
                "bad_ref", f"'{ref}' is not list:, detail:, no_list@, no_detail@, paging: or test:."
            )
    for kind in ("list", "detail"):
        refs, none = got.get(kind, []), reasons.get(f"no_{kind}")
        if kind == "detail" and len(refs) > 1:
            bad("detail_twice", "Name one detail route.")
        elif refs and none is not None:
            bad(f"{kind}_both", f"A feature cannot have a {kind} and say it has none.")
        elif not refs and none is None:
            bad(
                f"{kind}_ref",
                f"Name the {kind} route ({kind}:<route>) or say why not (no_{kind}@).",
            )
        elif none is not None and len(none.strip()) < MIN_REASON:
            bad("no_reason", f"Say why there is no {kind} (a short sentence).")
        for route in refs:
            op = system.operation(route, "GET") if route in system.routes() else None
            if route not in system.routes():
                bad("route_missing", f"There is no route named '{route}'.")
            elif op is None:
                bad(f"{kind}_missing", f"{route} has no GET operation in the OpenAPI document.")
            else:
                described = shape(system, op)
                if kind == "list" and not described.startswith(("array", "paged")):
                    bad(
                        "list_shape",
                        f"GET {route} is documented as {described}, a single record; "
                        "a list is an array or a paged object.",
                    )
                if kind == "detail" and described.startswith(("array", "paged", "none")):
                    bad(
                        "detail_shape", f"GET {route} is documented as {described}, not one record."
                    )
                for param in _id_params(op):
                    if param.get("schema", {}).get("format") != "uuid":
                        bad("id_not_public", f"{route} addresses a record by '{param['name']}'.")
    declared = got.get("paging", [])
    if got.get("list"):
        if len(declared) != 1 or declared[0] not in KINDS:
            bad("paging_ref", f"Declare exactly one paging:<{'|'.join(KINDS)}>.")
        else:
            for route in got["list"]:
                op = system.operation(route, "GET")
                if op is not None and paging_of(op) != declared[0]:
                    bad(
                        "paging_mismatch",
                        f"The claim says '{declared[0]}' but the OpenAPI parameters of {route} "
                        f"say '{paging_of(op)}'.",
                    )
            if declared[0] == "unpaged" and len(reasons.get("paging", "").strip()) < MIN_REASON:
                bad("no_reason", "Say why an unpaged list stays bounded (a short sentence).")
    elif declared:
        bad("paging_unused", "There is no list to page.")
    auth = feature.claims.get("authorization")
    if auth is not None and auth.state == "provided":
        for ref in auth.refs:
            if not ref.startswith("route:"):
                continue
            route = ref.partition(":")[2]
            for method in WRITES:
                if method not in _methods(system, route):
                    continue
                op = system.operation(route, method)
                if op is None:
                    bad("op_missing", f"{method} {route} is not in the OpenAPI document.")
                elif not any(code.startswith("2") for code in op.get("responses", {})):
                    bad("response_missing", f"{method} {route} documents no success response.")
    return found


def _methods(system, route) -> set[str]:
    pattern = system.routes().get(route)
    return {r["method"] for r in system.permission_matrix() if r["path"] == pattern}


def static(feature, claim, root) -> list[dict]:
    """CI: the proving tests exist."""
    return features.static_test_refs(feature, claim, root, "rest")


features.register_verifier("rest", verify, facts=facts, static=static)
