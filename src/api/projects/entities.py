"""Project entities offered to the universal query engine (core.entities)."""

from core import entities
from workspaces.models import Role

from .models import Project

entities.register(
    entities.Entity(
        key="projects",
        label="Projects",
        roles=(Role.ORGANIZER, Role.ADMIN),
        base=lambda event, user: Project.objects.filter(event=event).select_related(
            "track", "team", "created_by"
        ),
        default_sort=("name",),
        search_fields=("name", "description", "track", "team", "created_by"),
        board_field="track",
        calendar_fields=("created_at",),
        fields=(
            entities.Field("name", entities.TEXT, "name", "Project"),
            entities.Field(
                "description",
                entities.TEXT,
                "description",
                "Description",
                default=False,
                sortable=False,
            ),
            entities.Field("track", entities.TEXT, "track__name", "Track", groupable=True),
            entities.Field("team", entities.TEXT, "team__name", "Team"),
            # lets a screen choose a team by its name without showing or asking for its id
            entities.Field(
                "team_id",
                entities.UUID,
                "team__public_id",
                "Team reference",
                default=False,
                sortable=False,
                filterable=False,
            ),
            entities.Field("created_by", entities.TEXT, "created_by__username", "Created by"),
            entities.Field(
                "gallery_visible", entities.BOOL, "gallery_visible", "In gallery", groupable=True
            ),
            entities.Field(
                "gallery_blocked",
                entities.BOOL,
                "gallery_blocked",
                "Blocked",
                default=False,
                groupable=True,
            ),
            entities.Field("created_at", entities.DATE, "created_at", "Created"),
        ),
    )
)
