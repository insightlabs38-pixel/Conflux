"""Features of events (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="event",
        label="Event",
        model="events.Event",
        claims={"identity": provided("field:public_id", "route:event-detail")},
        lifecycle=Lifecycle(
            "choice",
            field="status",
            initial=("draft",),
            transitions="events.views:STATUS_FLOW",
            terminal=("archived",),
            via=("events.views.EventStatusView",),
        ),
    )
)
register_feature(
    Feature(
        key="track",
        label="Track",
        model="events.Track",
        claims={"identity": provided("field:public_id", "route:track-detail")},
        lifecycle=Lifecycle(
            "none", note="Edited in place and deleted (track.deleted); position orders it."
        ),
    )
)
register_feature(
    Feature(
        key="application",
        label="Registration application",
        model="events.EventApplication",
        claims={"identity": provided("field:public_id", "route:event-application-decide")},
        lifecycle=Lifecycle(
            "choice",
            field="status",
            initial=("pending", "approved", "waitlisted"),
            transitions={
                "pending": ("approved", "waitlisted", "rejected"),
                "waitlisted": ("approved", "rejected"),
            },
            terminal=("approved", "rejected"),
            via=("events.registration.decide_application",),
        ),
    )
)
register_feature(
    Feature(
        key="announcement",
        label="Announcement",
        model="events.Announcement",
        claims={"identity": provided("field:public_id", "route:announcement-detail")},
        lifecycle=Lifecycle(
            "timestamp",
            field="hidden_at",
            states=(("visible", "Visible"), ("hidden", "Hidden")),
            initial=("visible",),
            transitions={"visible": ("hidden",)},
            terminal=("hidden",),
            via=("communications.moderation.review_source",),
        ),
    )
)
