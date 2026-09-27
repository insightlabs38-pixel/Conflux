"""VS25: introspects the real DRF URL tree's `get_permissions()` to report
which workspace roles each (view, HTTP method) pair actually allows --
read directly from the same `core.permissions.HasWorkspaceRole`/
`require_roles` objects every view already uses to enforce access, so this
can never drift from a separately hand-maintained description of it.
"""

from types import SimpleNamespace

from django.urls import get_resolver
from rest_framework.permissions import AllowAny, IsAuthenticated
from workspaces.models import Role

from .permissions import HasWorkspaceRole, IsWorkspaceMember

_HTTP_METHODS = ("get", "post", "put", "patch", "delete")
_ALL_ROLES = tuple(Role.values)


def _walk(patterns, prefix=""):
    for entry in patterns:
        full = prefix + str(entry.pattern)
        sub_patterns = getattr(entry, "url_patterns", None)
        if sub_patterns is not None:
            yield from _walk(sub_patterns, full)
        else:
            yield full, entry


def _access_for_permission(perm):
    """(kind, roles) for one permission instance this tool recognizes, or
    (None, None) for a class it doesn't -- callers must treat that as "I
    can't vouch for this endpoint", never as "unrestricted".
    """
    if isinstance(perm, HasWorkspaceRole):
        return "roles", tuple(perm.roles)
    if isinstance(perm, IsWorkspaceMember):
        return "roles", _ALL_ROLES
    if isinstance(perm, IsAuthenticated):
        return "any_authenticated", None
    if isinstance(perm, AllowAny):
        return "public", None
    return None, None


def _combine(perms):
    """DRF ANDs every permission in the list; a role-scoped permission is
    always the binding constraint when one is present (the others in this
    codebase only ever widen membership requirements, never narrow a role
    set further -- see the module docstring's "no view stacks more than
    one" survey).
    """
    kinds = set()
    roles = None
    unrecognized = False
    for perm in perms:
        kind, perm_roles = _access_for_permission(perm)
        if kind is None:
            unrecognized = True
            continue
        kinds.add(kind)
        if kind == "roles":
            roles = set(perm_roles) if roles is None else roles & set(perm_roles)
    if "roles" in kinds:
        return {"access": "roles", "roles": sorted(roles or ()), "unrecognized": unrecognized}
    if "any_authenticated" in kinds:
        return {"access": "any_authenticated", "roles": [], "unrecognized": unrecognized}
    if "public" in kinds:
        return {"access": "public", "roles": [], "unrecognized": unrecognized}
    return {"access": "unknown", "roles": [], "unrecognized": True}


def build_permission_matrix():
    """One entry per (registered DRF view, HTTP method) pair actually wired
    into the URL tree, each reporting the exact access `get_permissions()`
    would compute for that method on a fresh instance -- a fake request
    carrying only `.method` is enough since every `get_permissions()`
    override in this codebase branches on that alone (never on kwargs, the
    user, or anything else).
    """
    entries = []
    for path, url_pattern in _walk(get_resolver().url_patterns):
        view_class = getattr(url_pattern.callback, "view_class", None)
        if view_class is None:
            continue
        resource = view_class.__module__.split(".")[0]
        for method in _HTTP_METHODS:
            if not hasattr(view_class, method):
                continue
            view = view_class()
            view.request = SimpleNamespace(method=method.upper())
            view.kwargs = {}
            try:
                combined = _combine(view.get_permissions())
            except Exception:
                combined = {"access": "unknown", "roles": [], "unrecognized": True}
            entries.append(
                {
                    "resource": resource,
                    "view": view_class.__name__,
                    "path": path,
                    "method": method.upper(),
                    **combined,
                }
            )
    entries.sort(key=lambda e: (e["resource"], e["path"], e["method"]))
    return entries
