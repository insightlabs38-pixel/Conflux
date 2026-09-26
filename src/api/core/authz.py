"""Central server-side authorization decisions.

Every workspace-scoped view routes its role check through here rather than
inlining `request.user.is_...` checks, so isolation rules (e.g. "a judge
cannot read a peer's scores") have exactly one place they can go wrong and
one place tests can pin down.
"""

from __future__ import annotations


def roles_for(user, workspace):
    """Return the frozenset of Membership roles `user` holds in `workspace`.

    A platform superuser is treated as holding every role in every workspace
    without needing a Membership row, matching Django's usual superuser
    bypass semantics.
    """
    if workspace is None or user is None or not getattr(user, "is_authenticated", False):
        return frozenset()

    from workspaces.models import Role

    if getattr(user, "is_superuser", False):
        return frozenset(Role.values)

    from workspaces.models import Membership

    return frozenset(
        Membership.objects.filter(user=user, workspace=workspace).values_list("role", flat=True)
    )


def has_any_role(user, workspace, *roles):
    if not roles:
        return False
    return bool(roles_for(user, workspace) & set(roles))


def is_workspace_member(user, workspace):
    return bool(roles_for(user, workspace))
