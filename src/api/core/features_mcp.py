"""Verifier for the `mcp` property (PD-F003-B02-T05): the MCP tools that reach a feature.

The MCP adapter (`mcp_adapter.tools.TOOLS`) is a catalogue of tools, each one existing API route
called with the credential's own authority: it adds no capability, so authorization, scoping,
validation and audit are what the route already enforces. A feature either has tools in that
catalogue or says why an agent has nothing to do with it, and a claim is held to the catalogue:

- `tool:<name>` (one or more): the tool is registered, its route is one of the routes the feature
  claims under `authorization`, the method is one the permission matrix lists for it and the path
  arguments the tool takes are the route's own; the claimed tools equal the derived set (every
  tool whose route is the feature's), so a tool added for a feature without a claim fails. A
  write tool must reach a route the feature audits (`write:<route>:<METHOD>=` under `audit`) that
  is gated by roles, so an agent cannot change what a person in no role could not.
- `test:<path>::<name>`: the proof, a test that calls the tools through the endpoint (CI checks
  it exists).
- `no_mcp@<reason>`: no tool reaches the feature, and why; a feature whose tools are owed is
  `planned` with the owning task.

A tool whose route no feature claims is named in `OUTSIDE` with the reason, so a new tool cannot
appear unowned (`tests/integration/test_feature_mcp.py`). The report lists each tool as a read or a
write with the route it calls.
"""

import re

from . import features
from .features import problem
from .features_audit import parse as parse_audit

MIN_REASON = 20
CATALOGUE = "mcp_adapter.tools:TOOLS"
ARGUMENTS = "mcp_adapter.tools:PATH_ARG_NAMES"

# Tools whose route is claimed by no feature, and why. They are read tools over routes of domains
# the registry does not claim yet; each is still held by the route's own authorization.
OUTSIDE = {
    "plan_progress": "reads a judging route that no feature claims yet",
    "plan_results": "reads a results route that no feature claims yet",
    "voting_results": "reads a voting route that no feature claims yet",
    "judge_workload": "reads a judging route that no feature claims yet",
    "event_analytics": "reads an analytics route that no feature claims yet",
    "list_exception_requests": "reads a deadline route that no feature claims yet",
    "list_result_corrections": "reads a results route that no feature claims yet",
    "mentor_request_queue": "reads a mentoring route that no feature claims yet",
    "add_mentor_note": "writes a mentoring route that no feature claims yet",
}


def parse(claim):
    tools, tests, reasons, other = [], [], [], []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        head, _, reason = ref.partition("@")
        if kind == "tool":
            tools.append(rest)
        elif kind == "test":
            tests.append(rest)
        elif head == "no_mcp":
            reasons.append(reason)
        else:
            other.append(ref)
    return tools, tests, reasons, other


def catalogue(system) -> dict:
    return {tool.name: tool for tool in (system.resolve(CATALOGUE) or [])}


def feature_routes(feature) -> set[str]:
    auth = feature.claims.get("authorization")
    if auth is None or auth.state != "provided":
        return set()
    return {r.partition(":")[2] for r in auth.refs if r.startswith("route:")}


def feature_tools(feature, system) -> set[str]:
    """Every tool of the catalogue that calls one of the feature's routes."""
    routes = feature_routes(feature)
    return {name for name, tool in catalogue(system).items() if tool.url_name in routes}


def facts(feature, system) -> dict:
    claim = feature.claims.get("mcp")
    if claim is None or claim.state != "provided":
        return {}
    tools, _, reasons, _ = parse(claim)
    if reasons:
        return {"mcp": "no tool", "why": reasons[0]}
    listed = catalogue(system)
    rows = [
        f"{name} ({'read' if listed[name].read_only else 'write'}): "
        f"{listed[name].method} {listed[name].url_name}"
        for name in tools
        if name in listed
    ]
    return {"tools": rows}


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="mcp"))

    tools, tests, reasons, other = parse(claim)
    for ref in other:
        bad("bad_ref", f"'{ref}' is not tool:<name>, test: or no_mcp@.")
    listed = catalogue(system)
    derived = feature_tools(feature, system)
    if reasons:
        if tools or tests:
            bad("both", "A feature cannot have MCP tools and say it has none.")
        if len(reasons) > 1 or len(reasons[0].strip()) < MIN_REASON:
            bad("no_reason", "Say once why no tool reaches this feature (a sentence).")
        for name in sorted(derived):
            bad("mcp_exists", f"The catalogue has the tool '{name}' for this feature; claim it.")
        return found
    if not tools:
        bad("no_tool", "Name each MCP tool (tool:<name>) or say why none (no_mcp@).")
    if tools and not tests:
        bad("no_test", "Name the test that calls the tools (test:<path>::<name>).")
    for ref in tests:
        if not re.fullmatch(r"tests/[\w./-]+\.py::test_\w+", ref):
            bad("test_ref", f"'{ref}' is not a test (tests/<file>.py::test_<name>).")
    if tools and not listed:
        bad("catalogue_missing", f"The MCP catalogue '{CATALOGUE}' cannot be read.")
        return found
    routes = feature_routes(feature)
    audit = feature.claims.get("audit")
    audited = parse_audit(audit)[0] if audit is not None and audit.state == "provided" else []
    arg_names = system.resolve(ARGUMENTS) or {}
    matrix = system.permission_matrix()
    seen = set()
    for name in tools:
        tool = listed.get(name)
        if name in seen:
            bad("tool_twice", f"'{name}' is claimed twice.")
        seen.add(name)
        for other_feature in features.FEATURES.values():
            other_claim = other_feature.claims.get("mcp")
            if (
                other_feature.key != feature.key
                and other_claim is not None
                and other_claim.state == "provided"
                and name in parse(other_claim)[0]
            ):
                bad("tool_shared", f"'{name}' is also claimed by '{other_feature.key}'.")
        if tool is None:
            bad("tool_unknown", f"'{name}' is not a registered MCP tool.")
            continue
        if tool.url_name not in routes:
            bad(
                "tool_foreign", f"'{name}' calls {tool.url_name}, not one of this feature's routes."
            )
            continue
        pattern = system.routes().get(tool.url_name)
        rows = [r for r in matrix if r["path"] == pattern and r["method"] == tool.method]
        if not rows:
            bad("method_unknown", f"{tool.method} {tool.url_name} is not in the permission matrix.")
        route_args = {n for _, n in system.converters(tool.url_name)}
        for arg in tool.path_args:
            if arg_names.get(arg, arg) not in route_args:
                bad("path_arg", f"'{name}' takes '{arg}', which {tool.url_name} has no place for.")
        if not tool.read_only:
            if not any(
                route == tool.url_name and method == tool.method for route, method, _, _ in audited
            ):
                bad(
                    "write_unaudited",
                    f"'{name}' writes {tool.url_name}, which the feature does not audit.",
                )
            if rows and not all(r["access"] == "roles" and r["roles"] for r in rows):
                bad("write_ungated", f"'{name}' writes a route that is not gated by roles.")
    for name in sorted(derived - set(tools)):
        bad("tool_unclaimed", f"The catalogue has the tool '{name}' for this feature; claim it.")
    return found


def static(feature, claim, root) -> list[dict]:
    return features.static_test_refs(feature, claim, root, "mcp")


features.register_verifier("mcp", verify, facts=facts, static=static)
