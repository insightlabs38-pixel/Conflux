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
            entities.Field("track", entities.TEXT, "track__name", "Track"),
            entities.Field("team", entities.TEXT, "team__name", "Team"),
            entities.Field("created_by", entities.TEXT, "created_by__username", "Created by"),
            entities.Field("gallery_visible", entities.BOOL, "gallery_visible", "In gallery"),
            entities.Field(
                "gallery_blocked", entities.BOOL, "gallery_blocked", "Blocked", default=False
            ),
            entities.Field("created_at", entities.DATE, "created_at", "Created"),
        ),
    )
)
