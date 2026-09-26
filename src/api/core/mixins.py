from django.shortcuts import get_object_or_404


class WorkspaceLookupMixin:
    """Resolves `self.get_workspace()` from a `workspace_public_id` URL kwarg
    before permission checks run, so `HasWorkspaceRole`/`IsWorkspaceMember`
    can evaluate role membership against the right tenant. Shared by every
    app with workspace-scoped endpoints (workspaces, audit, and later
    event/stage/policy views) to keep the lookup identical everywhere.
    """

    def get_workspace(self):
        from workspaces.models import Workspace

        if not hasattr(self, "_workspace"):
            self._workspace = get_object_or_404(
                Workspace, public_id=self.kwargs["workspace_public_id"]
            )
        return self._workspace
