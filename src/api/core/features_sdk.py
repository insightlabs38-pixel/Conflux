"""Verifier for the `sdk` property (PD-F003-B01-T07): how a feature appears in the generated SDKs.

Both SDKs (`sdks/python`, `sdks/typescript`) are generated from the OpenAPI document of the
running code, so a feature's operations are the operations of the routes it claims under
`authorization`, every method the permission matrix lists for them. A `provided` claim says the
feature is generated into both clients (`generated:python`, `generated:typescript`) and names the
proof (`test:`), and the verifier derives the rest:

- every operation of those routes is in the OpenAPI document with an operation id, unique in the
  document (the id is what both SDKs and every typed client call by);
- the report lists each operation with the response type the TypeScript client gives it, derived
  from the document (`Track[]`, `Event`, `null` for no body);
- CI (`check_static`, which has the source tree): each operation id is in both generated files
  with the right method and path, and the TypeScript response type of each operation equals the
  type derived from the OpenAPI document, so a list documented as a single record, a renamed
  schema or a stale SDK fails here.
"""

import re
from pathlib import Path

from . import features
from .features import problem

WRITES = ("POST", "PUT", "PATCH", "DELETE")
TARGETS = ("python", "typescript")


def parse(claim):
    targets, other = [], []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        if kind == "generated":
            targets.append(rest)
        else:
            other.append(ref)
    return targets, other


def ts_type(system, op) -> str | None:
    """The TypeScript response type of an operation, as the generator writes it, or None when the
    document does not describe the response by a named schema (a primitive or free-form body)."""
    codes = [c for c in op.get("responses", {}) if c.startswith("2")]
    for code in sorted(codes):
        content = (op["responses"][code] or {}).get("content", {})
        schema = (content.get("application/json") or {}).get("schema")
        if schema is None:
            continue
        if "$ref" in schema:
            return schema["$ref"].rsplit("/", 1)[-1]
        if schema.get("type") == "array" and "$ref" in schema.get("items", {}):
            return schema["items"]["$ref"].rsplit("/", 1)[-1] + "[]"
        return None
    return "null"


def operations(feature, system):
    """(route, METHOD, OpenAPI operation or None) for every method of every claimed route."""
    auth = feature.claims.get("authorization")
    if auth is None or auth.state != "provided":
        return []
    found = []
    for ref in auth.refs:
        if not ref.startswith("route:"):
            continue
        route = ref.partition(":")[2]
        pattern = system.routes().get(route)
        methods = sorted({r["method"] for r in system.permission_matrix() if r["path"] == pattern})
        found += [(route, method, system.operation(route, method)) for method in methods]
    return found


def _counts(system) -> dict:
    counts: dict[str, int] = {}
    for path in system.openapi()["paths"].values():
        for method, op in path.items():
            if method in ("get", "post", "put", "patch", "delete") and "operationId" in op:
                counts[op["operationId"]] = counts.get(op["operationId"], 0) + 1
    return counts


def facts(feature, system) -> dict:
    claim = feature.claims.get("sdk")
    if claim is None or claim.state != "provided":
        return {}
    listed = []
    for route, method, op in operations(feature, system):
        if op is None:
            continue
        typed = ts_type(system, op)
        listed.append(f"{method} {route}: {typed if typed is not None else 'value'}")
    return {"operations": listed, "count": len(listed)}


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="sdk"))

    if system.model(feature.model) is None:
        return found
    targets, other = parse(claim)
    if not any(r.startswith("test:") for r in other):
        bad("no_test", "Name the test that calls each operation through the generated SDK (test:).")
    for ref in other:
        if not ref.startswith("test:"):
            bad("bad_ref", f"'{ref}' is not generated: or test:.")
    for target in targets:
        if target not in TARGETS:
            bad("bad_target", f"'{target}' is not one of {', '.join(TARGETS)}.")
    for target in TARGETS:
        if target not in targets:
            bad("target_missing", f"The claim must say the feature is generated into {target}.")
    listed = operations(feature, system)
    if not listed:
        bad("no_operations", "The feature claims no routes under authorization to generate from.")
    counts = _counts(system)
    for route, method, op in listed:
        if op is None:
            bad("op_missing", f"{method} {route} is not in the OpenAPI document.")
        elif "operationId" not in op:
            bad("op_id", f"{method} {route} has no operation id.")
        elif counts.get(op["operationId"], 0) != 1:
            bad("op_id_twice", f"The operation id of {method} {route} is not unique.")
    return found


def _ts_response(text: str, op_id: str) -> str | None:
    """The `response:` type of an operation in the generated TypeScript interface."""
    match = re.search(
        rf"^  {re.escape(op_id)}:\s*\{{\s*request:(.*?)^  \}};", text, flags=re.S | re.M
    )
    if match is None:
        return None
    body = re.search(r"response: ([^;]+);", match.group(1))
    return body.group(1).strip() if body else None


def static(feature, claim, root) -> list[dict]:
    """CI: the operations are in both generated files and the TypeScript types match OpenAPI."""
    from .features import System

    found = features.static_test_refs(feature, claim, root, "sdk")
    system = System()
    py_file = Path(root) / "sdks/python/conflux_sdk/generated.py"
    ts_file = Path(root) / "sdks/typescript/generated.ts"
    if not py_file.is_file() or not ts_file.is_file():
        return found + [
            problem(
                "sdk_missing",
                "The generated SDK files are not in the source tree.",
                feature=feature.key,
                prop="sdk",
            )
        ]
    py_text, ts_text = py_file.read_text(), ts_file.read_text()
    for route, method, op in operations(feature, system):
        if op is None or "operationId" not in op:
            continue
        op_id = op["operationId"]
        label = f"{method} {route}"

        def bad(code, message):
            found.append(problem(code, message, feature=feature.key, prop="sdk"))

        if not re.search(rf"'{re.escape(op_id)}': \{{'method': '{method}'", py_text):
            bad("python_missing", f"{label} ({op_id}) is not in the Python SDK with {method}.")
        if not re.search(rf"^  {re.escape(op_id)}:\s*\{{\s*method: \"{method}\"", ts_text, re.M):
            bad("ts_missing", f"{label} ({op_id}) is not in the TypeScript operations.")
        expected = ts_type(system, op)
        got = _ts_response(ts_text, op_id)
        if got is None:
            bad("ts_types_missing", f"{label} ({op_id}) has no TypeScript response type.")
        elif expected is not None and got != expected:
            bad(
                "ts_type_mismatch",
                f"{label}: the TypeScript client returns '{got}' but OpenAPI says '{expected}'.",
            )
    return found


features.register_verifier("sdk", verify, facts=facts, static=static)
