"""People entity offered to the universal query engine (core.entities).

Only the people who hold a role in the event's workspace, and only their username: an organizer
picking someone (for example to preview what they can do) never needs to know or type an id.
"""

from core import entities
from workspaces.models import Role

from .models import User

entities.register(
    entities.Entity(
        key="people",
        label="People",
        roles=(Role.ORGANIZER, Role.ADMIN),
        base=lambda event, user: User.objects.filter(
            memberships__workspace_id=event.workspace_id
        ).distinct(),
        default_sort=("username",),
        fields=(entities.Field("username", entities.TEXT, "username", "Person"),),
    )
)
