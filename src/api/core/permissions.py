from rest_framework.permissions import BasePermission

from .authz import has_any_role, is_workspace_member


class WorkspaceScopedPermission(BasePermission):
    """Base for permissions that need the workspace resolved from the view.

    Views expose the workspace they act on via `get_workspace(request, **kwargs)`
    (looked up from a public ID in the URL, typically) and views a permission
    denial as authorization failing closed: no workspace resolvable means no
    access, never a silent pass-through.
    """

    def _resolve_workspace(self, request, view):
        get_workspace = getattr(view, "get_workspace", None)
        if get_workspace is None:
            return None
        workspace = get_workspace()
        if workspace is not None:
            request.workspace = workspace
        return workspace


class IsWorkspaceMember(WorkspaceScopedPermission):
    message = "You are not a member of this workspace."

    def has_permission(self, request, view):
        workspace = self._resolve_workspace(request, view)
        return is_workspace_member(request.user, workspace)


class HasWorkspaceRole(WorkspaceScopedPermission):
    """Subclass and set `roles` (or use `require_roles(...)`) to require one
    of a specific set of workspace roles rather than mere membership.
    """

    roles: tuple[str, ...] = ()
    message = "You do not have a role that permits this action."

    def has_permission(self, request, view):
        workspace = self._resolve_workspace(request, view)
        return has_any_role(request.user, workspace, *self.roles)


def require_roles(*roles):
    """Build a `HasWorkspaceRole` permission class scoped to `roles`."""
    return type("ScopedWorkspaceRole", (HasWorkspaceRole,), {"roles": tuple(roles)})
