"""Verifier for the `authorization` property (PD-F003-B01-T03): authorization and scope rules.

Authorization is decided on the server, once, and the platform already records it: the permission
matrix reads the role gates the code really applies (`core.permission_matrix`). A `provided` claim
states who may read and who may write a feature and where its records are scoped, and the verifier
holds the claim to the system:

- `route:<url name>` (one or more): the feature's API routes. Each must exist, carry the workspace
  in its URL (and the event, for event scope), appear in the permission matrix and be gated by
  roles; a route open to anyone signed in or the public needs an explicit `open:<route>` ref.
- `scope:event` or `scope:workspace`: where records live, confirmed by the model's own foreign
  keys (a chain to `events.Event` or `workspaces.Workspace`).
- `readers:<roles>` and `writers:<roles>`: who the matrix says may reach the GET routes and the
  writing routes (`members` for every role, `none` for no route). The claim must equal the matrix,
  so widening access without updating the claim fails.
- `own:<rule>`: required exactly when roles other than organizers and admins may write; it names
  the object-level rule the view enforces (`project_member`, `team_member`, `self`).
- `test:<path>::<name>`: adversarial tests that a wrong role, another workspace and another
  member's object are refused (a CI check confirms the file and the test exist).

The report also carries an Explanation (`core.explain`) of who can do what, derived from the
matrix, so the page says it in words and never decides anything.
"""

from workspaces.models import Role

from . import explain, features
from .features import problem

ALL_ROLES = frozenset(Role.values)
ORGANIZER_ROLES = frozenset({Role.ADMIN.value, Role.ORGANIZER.value})
OWN_RULES = ("project_member", "team_member", "self")
WRITES = ("POST", "PUT", "PATCH", "DELETE")


def _roles_text(roles: set[str]) -> str:
    if roles == ALL_ROLES:
        return "members"
    return ",".join(sorted(roles)) if roles else "none"


def _matrix_rows(system, route_name):
    pattern = system.routes().get(route_name)
    return [r for r in system.permission_matrix() if r["path"] == pattern] if pattern else []


def derive(feature, claim, system) -> dict:
    """What the permission matrix says about the claimed routes."""
    readers, writers, per_route, open_routes = set(), set(), [], []
    for ref in claim.refs:
        kind, _, name = ref.partition(":")
        if kind != "route":
            continue
        for row in _matrix_rows(system, name):
            if row["access"] == "roles":
                roles = {str(r.value if hasattr(r, "value") else r) for r in row["roles"]}
            else:
                roles = set()
                open_routes.append(f"{name} {row['method']} ({row['access']})")
            (readers if row["method"] == "GET" else writers).update(roles)
            per_route.append((name, row["method"], row["access"], roles))
    return {"readers": readers, "writers": writers, "routes": per_route, "open": open_routes}


def facts(feature, system) -> dict:
    claim = feature.claims.get("authorization")
    if claim is None or claim.state != "provided":
        return {}
    got = derive(feature, claim, system)
    model = system.model(feature.model)
    scope = next((r.partition(":")[2] for r in claim.refs if r.startswith("scope:")), "")
    target = {"event": "events.Event", "workspace": "workspaces.Workspace"}.get(scope)
    path = system.fk_path(model, target) if model is not None and target else None
    reasons = []
    for name, method, access, roles in got["routes"]:
        who = (
            "anyone signed in"
            if access == "any_authenticated"
            else "anyone"
            if access == "public"
            else _roles_text(roles)
        )
        reasons.append(
            explain.reason(
                "role_gate", f"{method} {name}: {who}", facts={"route": name, "method": method}
            )
        )
    own = [r.partition(":")[2] for r in claim.refs if r.startswith("own:")]
    if own:
        reasons.append(
            explain.reason(
                "object_rule",
                f"Roles other than organizers and admins reach only records they own ({own[0]}).",
                severity="warning",
            )
        )
    can_write = _roles_text(got["writers"])
    summary = (
        f"Read: {_roles_text(got['readers'])}. Change: {can_write}. "
        f"Records are scoped to their {scope or 'workspace'}."
    )
    return {
        "readers": _roles_text(got["readers"]),
        "writers": can_write,
        "scope_path": [system.model(label)._meta.object_name for label in path] if path else [],
        "explanation": explain.explanation("allowed", summary, reasons),
    }


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="authorization"))

    model = system.model(feature.model)
    if model is None:
        return found
    refs = {k: [] for k in ("route", "scope", "readers", "writers", "own", "open", "test")}
    for ref in claim.refs:
        kind, _, value = ref.partition(":")
        if kind in refs:
            refs[kind].append(value)
        else:
            bad(
                "bad_ref",
                f"'{ref}' is not route:, scope:, readers:, writers:, own:, open: or test:.",
            )
    if not refs["route"]:
        bad("no_routes", "Name the routes this feature is reached through (route:<url name>).")
    if len(refs["scope"]) != 1 or refs["scope"][0] not in ("event", "workspace"):
        bad("scope_ref", "Declare exactly one scope: scope:event or scope:workspace.")
    for kind in ("readers", "writers"):
        if len(refs[kind]) != 1:
            bad(f"{kind}_ref", f"Declare exactly one {kind}:<roles>.")
    if not refs["test"]:
        bad(
            "no_test",
            "Name an adversarial test (a wrong role, another workspace, another member's object).",
        )
    scope = refs["scope"][0] if len(refs["scope"]) == 1 else ""
    for name in refs["route"]:
        if name not in system.routes():
            bad("route_missing", f"There is no route named '{name}'.")
            continue
        params = {n for _, n in system.converters(name)}
        if "workspace_public_id" not in params:
            bad("route_tenant", f"Route '{name}' does not carry the workspace in its URL.")
        if scope == "event" and "event_public_id" not in params:
            bad("route_scope", f"Route '{name}' does not carry the event in its URL.")
        if not _matrix_rows(system, name):
            bad("route_unmatrixed", f"Route '{name}' is not in the permission matrix.")
    if scope in ("event", "workspace"):
        target = "events.Event" if scope == "event" else "workspaces.Workspace"
        if system.fk_path(model, target) is None:
            bad("scope_path", f"The model has no chain of foreign keys to {target}.")
    got = derive(feature, claim, system)
    for name, method, access, roles in got["routes"]:
        label = f"{method} {name}"
        if access not in ("roles", "any_authenticated", "public"):
            bad("access_unknown", f"{label} has an access rule the matrix cannot vouch for.")
        elif access != "roles" and f"{name}" not in refs["open"]:
            bad(
                "route_open",
                f"{label} is open to {'anyone' if access == 'public' else 'anyone signed in'}; "
                f"acknowledge it with open:{name}.",
            )
    for kind in ("readers", "writers"):
        if len(refs[kind]) == 1 and got["routes"]:
            derived_text = _roles_text(got[kind])
            declared = (
                ",".join(sorted(refs[kind][0].split(",")))
                if refs[kind][0] not in ("members", "none")
                else refs[kind][0]
            )
            if declared != derived_text:
                bad(
                    f"{kind}_mismatch",
                    f"The claim says {kind} are '{refs[kind][0]}' "
                    f"but the permission matrix says '{derived_text}'.",
                )
    extra = got["writers"] - ORGANIZER_ROLES
    if extra and not refs["own"]:
        bad(
            "own_missing",
            "Roles other than organizers and admins may write; name the object rule (own:).",
        )
    if not extra and refs["own"]:
        bad(
            "own_unused",
            "Only organizers and admins write, so there is no object-level rule to declare.",
        )
    for rule in refs["own"]:
        if rule not in OWN_RULES:
            bad("own_ref", f"'{rule}' is not one of {', '.join(OWN_RULES)}.")
    return found


def static(feature, claim, root) -> list[dict]:
    return features.static_test_refs(feature, claim, root, "authorization")


features.register_verifier("authorization", verify, facts=facts, static=static)
