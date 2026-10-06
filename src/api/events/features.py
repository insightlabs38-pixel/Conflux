"""Features of events (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="event",
        label="Event",
        model="events.Event",
        claims={
            "identity": provided("field:public_id", "route:event-detail"),
            "validation": provided(
                "check:events.models.Event.clean",
                "check:events.views.EventStatusView",
                "constraint:events.Event.unique_event_slug_workspace",
                "test:tests/integration/test_event_consequences.py::test_opening_an_event_without_dates_is_refused_with_the_endpoints_reason",
            ),
            "authorization": provided(
                "route:event-list",
                "route:event-detail",
                "route:event-status",
                "scope:workspace",
                "readers:admin,organizer",
                "writers:admin,organizer",
                "test:tests/integration/test_event_creation_flow.py::test_only_organizers_create_events_from_a_format",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
            ),
        },
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
        claims={
            "identity": provided("field:public_id", "route:track-detail"),
            "validation": provided(
                "check:events.views.TrackListView",
                "constraint:events.Track.unique_track_name_event",
                "test:tests/integration/test_feature_validation.py::test_a_track_needs_a_name_and_a_unique_one",
            ),
            "authorization": provided(
                "route:track-list",
                "route:track-detail",
                "scope:event",
                "readers:members",
                "writers:admin,organizer",
                "test:tests/integration/test_event_tracks_api.py::test_participant_can_read_tracks_so_they_can_pick_one_for_a_project_but_not_create_one",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
            ),
        },
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
        claims={
            "identity": provided("field:public_id", "route:event-application-decide"),
            "validation": provided(
                "check:events.models.EventApplication.clean",
                "check:events.registration.decide_application",
                "constraint:events.EventApplication.unique_event_application",
                "test:tests/integration/test_event_registration.py::test_invite_only_registration_requires_a_valid_unspent_code",
            ),
            "authorization": provided(
                "route:event-application-list",
                "route:event-application-decide",
                "scope:event",
                "readers:admin,organizer",
                "writers:admin,organizer",
                "test:tests/integration/test_event_registration.py::test_application_mode_requires_organizer_decision",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
            ),
        },
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
        claims={
            "identity": provided("field:public_id", "route:announcement-detail"),
            "validation": provided(
                "check:events.views.AnnouncementListView",
                "test:tests/integration/test_feature_validation.py::test_an_announcement_needs_a_title_and_text_within_bounds",
            ),
            "authorization": provided(
                "route:announcement-list",
                "route:announcement-detail",
                "route:announcement-review",
                "scope:event",
                "readers:admin,organizer",
                "writers:admin,organizer",
                "test:tests/integration/test_announcements.py::test_organizer_manages_announcements_and_others_cannot",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
            ),
        },
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
