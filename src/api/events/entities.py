"""Event entities offered to the universal query engine (core.entities)."""

from core import entities
from workspaces.models import Role

from .models import EventApplication, RegistrationStatus

entities.register(
    entities.Entity(
        key="applications",
        label="Applications",
        roles=(Role.ORGANIZER, Role.ADMIN),
        base=lambda event, user: EventApplication.objects.filter(event=event).select_related(
            "user", "decided_by"
        ),
        default_sort=("waitlist_position", "created_at"),
        search_fields=("username", "note", "decided_by"),
        fields=(
            entities.Field("username", entities.TEXT, "user__username", "Applicant"),
            entities.Field(
                "status",
                entities.ENUM,
                "status",
                "Status",
                choices=tuple(RegistrationStatus.values),
                groupable=True,
            ),
            entities.Field("note", entities.TEXT, "note", "Note", sortable=False),
            entities.Field("waitlist_position", entities.NUMBER, "waitlist_position", "Waitlist"),
            entities.Field(
                "decided_by",
                entities.TEXT,
                "decided_by__username",
                "Decided by",
                default=False,
                groupable=True,
            ),
            entities.Field("decided_at", entities.DATE, "decided_at", "Decided", default=False),
            entities.Field("created_at", entities.DATE, "created_at", "Applied"),
        ),
    )
)
