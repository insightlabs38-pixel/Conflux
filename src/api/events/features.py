"""Features of events (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, planned, provided, register_feature

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
            "audit": provided(
                "write:event-list:POST=event.created",
                "write:event-detail:PATCH=event.updated",
                "write:event-detail:DELETE=event.deleted",
                "write:event-status:POST=event.status_changed",
                "test:tests/integration/test_feature_audit.py::test_each_declared_change_records_its_audit_action",
                "test:tests/integration/test_feature_audit.py::test_a_refused_change_leaves_no_audit_row",
            ),
            "idempotency": provided(
                "mode:event-list:POST=unique@events.Event.unique_event_slug_workspace",
                "mode:event-detail:PATCH=natural",
                "mode:event-detail:DELETE=natural",
                "mode:event-status:POST=natural",
                "test:tests/integration/test_feature_idempotency.py::test_a_repeated_change_does_what_its_declared_mode_says",
            ),
            "rest": provided(
                "list:event-list",
                "detail:event-detail",
                "paging:unpaged@bounded: a workspace runs a few dozen events and the list is the  "
                "organizer's index",
                "test:tests/integration/test_feature_rest.py::test_every_refusal_of_a_claimed_route_uses_the_shared_error_shape",
                "test:tests/integration/test_feature_rest.py::test_every_claimed_list_returns_what_its_schema_says",
            ),
            "sdk": provided(
                "generated:python",
                "generated:typescript",
                "test:tests/integration/test_feature_sdk.py::test_every_claimed_operation_works_through_the_generated_python_sdk",
            ),
            "search": provided(
                "no_query@read whole through the workspace's event list: a workspace runs a few "
                "dozen events, so a query over them is not offered",
            ),
            "ui_base": provided(
                "component:src/web/features/event-builder/EventDashboard.tsx",
                "component:src/web/features/event-builder/CreateEvent.tsx",
                "test:src/web/features/event-builder/EventDashboard.test.tsx",
                "test:src/web/features/event-builder/CreateEvent.test.tsx",
            ),
            "ui_advanced": provided(
                "uses:ConsequenceDialog@src/web/features/event-builder/EventDashboard.tsx",
                "uses:SchemaForm@src/web/features/event-builder/ConfigurationPanel.tsx",
            ),
            "bulk": provided(
                "no_bulk@the planner works inside one event, and an event is configured one at "
                "a time on its own screens",
            ),
            "cli": provided(
                "command:events list",
                "command:events get",
                "command:events create",
                "command:events update",
                "command:events status",
                "test:tests/integration/test_feature_cli.py::test_each_claimed_command_sends_the_request_its_operation_describes",
                "test:tests/test_admin_cli.py::test_cli_create_manage_export_preview_and_import_use_canonical_api",
            ),
            "mcp": provided(
                "no_mcp@an agent reads an event through its stages, projects and results; an "
                "event itself is configured by people",
            ),
            "event_as_code": provided(
                "section:event",
                "test:tests/integration/test_event_as_code.py::test_document_applies_to_an_empty_event_and_reproduces_the_source",
                "test:tests/integration/test_feature_eac.py::test_every_section_writes_exactly_the_rows_it_declares",
            ),
            "webhook": provided(
                "emit:event.created=event.created",
                "emit:event.deleted=event.deleted",
                "emit:event.status_changed=event.status_changed",
                "emit:event.updated=event.updated",
                "test:tests/integration/test_feature_webhook.py::test_each_audited_change_writes_the_outbox_event_its_claim_names",
            ),
            "archive": provided(
                "root@the archive is one event and restores as a new draft event, so the event "
                "is the root of every table",
                "test:tests/integration/test_feature_archive.py::test_the_event_is_the_root_and_restores_as_a_new_draft_event",
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
            "audit": provided(
                "write:track-list:POST=track.created",
                "write:track-detail:PATCH=track.updated",
                "write:track-detail:DELETE=track.deleted",
                "test:tests/integration/test_feature_audit.py::test_each_declared_change_records_its_audit_action",
                "test:tests/integration/test_feature_audit.py::test_a_refused_change_leaves_no_audit_row",
            ),
            "idempotency": provided(
                "mode:track-list:POST=unique@events.Track.unique_track_name_event",
                "mode:track-detail:PATCH=natural",
                "mode:track-detail:DELETE=natural",
                "test:tests/integration/test_feature_idempotency.py::test_a_repeated_change_does_what_its_declared_mode_says",
            ),
            "rest": provided(
                "list:track-list",
                "no_detail@a track is read in the event's track list and has no page of its own",
                "paging:unpaged@bounded: an event has a handful of tracks",
                "test:tests/integration/test_feature_rest.py::test_every_refusal_of_a_claimed_route_uses_the_shared_error_shape",
                "test:tests/integration/test_feature_rest.py::test_every_claimed_list_returns_what_its_schema_says",
            ),
            "sdk": provided(
                "generated:python",
                "generated:typescript",
                "test:tests/integration/test_feature_sdk.py::test_every_claimed_operation_works_through_the_generated_python_sdk",
            ),
            "search": provided(
                "no_query@read whole through its list: an event has a handful of tracks, so a "
                "query over them is not offered",
            ),
            "ui_base": provided(
                "component:src/web/features/event-builder/EventDashboard.tsx",
                "test:src/web/features/event-builder/EventDashboard.test.tsx",
            ),
            "ui_advanced": provided(
                "no_advanced@tracks are named and ordered inline in the event dashboard; there is "
                "nothing beyond the base screen",
            ),
            "bulk": provided(
                "no_bulk@tracks are few and ordered in place on the event dashboard; a batch "
                "over them adds nothing",
            ),
            "cli": provided(
                "no_cli@tracks are part of the event configuration and travel with events "
                "export and import; nothing is done per track",
            ),
            "mcp": provided(
                "no_mcp@tracks are part of the event configuration, which people set and agents "
                "do not change",
            ),
            "event_as_code": provided(
                "section:tracks",
                "test:tests/integration/test_event_as_code.py::test_document_applies_to_an_empty_event_and_reproduces_the_source",
                "test:tests/integration/test_feature_eac.py::test_every_section_writes_exactly_the_rows_it_declares",
            ),
            "webhook": provided(
                "emit:track.created=track.created",
                "emit:track.deleted=track.deleted",
                "emit:track.updated=track.updated",
                "test:tests/integration/test_feature_webhook.py::test_each_audited_change_writes_the_outbox_event_its_claim_names",
            ),
            "archive": provided(
                "table:events.track",
                "test:tests/integration/test_feature_archive.py::test_each_claimed_table_is_restored_with_its_rows",
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
            "audit": provided(
                "write:event-application-decide:POST=application.decided",
                "test:tests/integration/test_feature_audit.py::test_each_declared_change_records_its_audit_action",
                "test:tests/integration/test_feature_audit.py::test_a_refused_change_leaves_no_audit_row",
            ),
            "idempotency": provided(
                "mode:event-application-decide:POST=locked@events.registration.decide_application",
                "test:tests/integration/test_feature_idempotency.py::test_a_repeated_change_does_what_its_declared_mode_says",
            ),
            "rest": provided(
                "list:event-application-list",
                "no_detail@an application is read in the review queue, which filters by status",
                "paging:unpaged@bounded by the event's applicants and filtered with ?status=;  "
                "large queues are paged through the applications query entity",
                "test:tests/integration/test_feature_rest.py::test_every_refusal_of_a_claimed_route_uses_the_shared_error_shape",
                "test:tests/integration/test_feature_rest.py::test_every_claimed_list_returns_what_its_schema_says",
            ),
            "sdk": provided(
                "generated:python",
                "generated:typescript",
                "test:tests/integration/test_feature_sdk.py::test_every_claimed_operation_works_through_the_generated_python_sdk",
            ),
            "search": provided(
                "entity:applications",
                "fields:username,status,note,waitlist_position,decided_by,decided_at,created_at",
                "test:tests/integration/test_entity_query.py::test_every_registered_field_resolves_against_the_database",
            ),
            "ui_base": provided(
                "component:src/web/features/event-builder/RegistrationPanel.tsx",
                "test:src/web/features/event-builder/RegistrationPanel.test.tsx",
            ),
            "ui_advanced": provided(
                "uses:EntityGrid@src/web/features/event-builder/RegistrationPanel.tsx",
                "uses:NotesDialog@src/web/features/event-builder/RegistrationPanel.tsx",
            ),
            "bulk": planned(
                "PD-S012-B03-T08",
                "Registration decisions are made one at a time today; the planner has no action "
                "for a batch.",
            ),
            "cli": provided(
                "no_cli@registrations are reviewed by organizers on their own screens; the CLI "
                "administers events only",
            ),
            "mcp": provided(
                "no_mcp@registration review is a decision about a person that stays with "
                "organizers, not with an agent",
            ),
            "event_as_code": provided(
                "no_eac@registrations are runtime participant data and never part of the "
                "configuration document",
            ),
            "webhook": provided(
                "silent:application.decided@a decision concerns one person and no event type "
                "shows it to subscribers today",
                "test:tests/integration/test_feature_webhook.py::test_each_audited_change_writes_the_outbox_event_its_claim_names",
            ),
            "archive": provided(
                "excluded@registrations are personal data of applicants and are not part of the "
                "archive contract",
                "test:tests/integration/test_feature_archive.py::test_each_excluded_model_is_in_the_archives_exclusion_list_and_not_in_its_contract",
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
            "audit": provided(
                "write:announcement-list:POST=announcement.posted",
                "write:announcement-detail:DELETE=announcement.deleted",
                "write:announcement-review:POST=announcement.reviewed",
                "test:tests/integration/test_feature_audit.py::test_each_declared_change_records_its_audit_action",
                "test:tests/integration/test_feature_audit.py::test_a_refused_change_leaves_no_audit_row",
            ),
            "idempotency": provided(
                "mode:announcement-list:POST=keyed",
                "mode:announcement-detail:DELETE=natural",
                "mode:announcement-review:POST=locked@events.Announcement.version",
                "test:tests/integration/test_feature_idempotency.py::test_a_repeated_change_does_what_its_declared_mode_says",
                "test:tests/integration/test_feature_idempotency.py::test_a_keyed_change_runs_once_for_one_key_and_a_different_body_is_refused",
            ),
            "rest": provided(
                "list:announcement-list",
                "no_detail@an announcement is read in the event's list and has no page of its own",
                "paging:unpaged@bounded: an event has a handful of announcements, posted by  "
                "organizers",
                "test:tests/integration/test_feature_rest.py::test_every_refusal_of_a_claimed_route_uses_the_shared_error_shape",
                "test:tests/integration/test_feature_rest.py::test_every_claimed_list_returns_what_its_schema_says",
            ),
            "sdk": provided(
                "generated:python",
                "generated:typescript",
                "test:tests/integration/test_feature_sdk.py::test_every_claimed_operation_works_through_the_generated_python_sdk",
            ),
            "search": provided(
                "no_query@read whole through its list: an event has a handful of announcements, "
                "so a query over them is not offered",
            ),
            "ui_base": planned(
                "PD-S009-B02-T03",
                "No organizer screen posts announcements yet; they are read on the event site.",
            ),
            "ui_advanced": planned(
                "PD-S009-B02-T03",
                "No screen posts announcements yet, so nothing sits beyond one.",
            ),
            "bulk": provided(
                "no_bulk@announcements are posted one at a time to the event site; a batch "
                "makes no sense for them",
            ),
            "cli": provided(
                "no_cli@announcements are posted to the event site by organizers; the CLI "
                "administers events only",
            ),
            "mcp": provided(
                "tool:list_announcements",
                "tool:create_announcement",
                "test:tests/integration/test_mcp_adapter.py::test_a_write_tool_goes_through_the_normal_route_and_is_double_audited",
                "test:tests/integration/test_feature_mcp.py::test_each_claimed_tool_reaches_its_own_route_with_a_credential_limited_to_it",
            ),
            "event_as_code": provided(
                "no_eac@announcements are content posted during the event, not configuration of it",
            ),
            "webhook": provided(
                "emit:announcement.deleted=announcement.deleted",
                "emit:announcement.posted=announcement.posted",
                "silent:announcement.reviewed@a review decision on an announcement is internal "
                "to organizers; no event type exists for it",
                "test:tests/integration/test_feature_webhook.py::test_each_audited_change_writes_the_outbox_event_its_claim_names",
            ),
            "archive": provided(
                "excluded@announcements are content posted during the event and are not part of "
                "the archive contract",
                "test:tests/integration/test_feature_archive.py::test_each_excluded_model_is_in_the_archives_exclusion_list_and_not_in_its_contract",
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
