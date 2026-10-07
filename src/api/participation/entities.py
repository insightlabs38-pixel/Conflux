"""Team entity offered to the universal query engine (core.entities)."""

from core import entities
from workspaces.models import Role

from .models import Team

entities.register(
    entities.Entity(
        key="teams",
        label="Teams",
        roles=(Role.ORGANIZER, Role.ADMIN),
        base=lambda event, user: Team.objects.filter(event=event),
        default_sort=("name",),
        fields=(
            entities.Field("name", entities.TEXT, "name", "Team"),
            entities.Field("created_at", entities.DATE, "created_at", "Created"),
        ),
    )
)
