"""Features of communications (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, planned, provided, register_feature

register_feature(
    Feature(
        key="message",
        label="Message",
        model="communications.Message",
        claims={
            "identity": provided("field:public_id"),
            "validation": provided(
                "check:communications.models.Message.clean",
                "test:tests/integration/test_feature_validation.py::test_a_message_needs_a_known_audience_and_a_subject_and_leaves_nothing_behind",
            ),
            "authorization": provided(
                "route:message-list-create",
                "scope:event",
                "readers:admin,organizer",
                "writers:admin,organizer",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
            ),
            "audit": provided(
                "write:message-list-create:POST=message.sent",
                "test:tests/integration/test_feature_audit.py::test_each_declared_change_records_its_audit_action",
                "test:tests/integration/test_feature_audit.py::test_a_refused_change_leaves_no_audit_row",
            ),
            "idempotency": provided(
                "mode:message-list-create:POST=keyed",
                "test:tests/integration/test_feature_idempotency.py::test_a_repeated_change_does_what_its_declared_mode_says",
                "test:tests/integration/test_feature_idempotency.py::test_a_keyed_change_runs_once_for_one_key_and_a_different_body_is_refused",
            ),
            "rest": provided(
                "list:message-list-create",
                "no_detail@a message is read in the event's message history",
                "paging:offset",
                "test:tests/integration/test_feature_rest.py::test_every_refusal_of_a_claimed_route_uses_the_shared_error_shape",
                "test:tests/integration/test_feature_rest.py::test_every_claimed_list_returns_what_its_schema_says",
            ),
            "sdk": provided(
                "generated:python",
                "generated:typescript",
                "test:tests/integration/test_feature_sdk.py::test_every_claimed_operation_works_through_the_generated_python_sdk",
            ),
            "search": provided(
                "no_query@read through the offset-paged message history; recipients are searched "
                "in the inbox, not here",
            ),
            "ui_base": provided(
                "component:src/web/features/communications/CommunicationsPanel.tsx",
                "test:src/web/features/communications/CommunicationsPanel.test.tsx",
            ),
            "ui_advanced": provided(
                "no_advanced@a message is composed and sent in the base screen; delivery detail "
                "is in the inbox",
            ),
            "bulk": provided(
                "action:send=message.sent",
                "test:tests/integration/test_bulk_operations.py::test_full_preview_apply_and_retry_are_atomic_and_audited",
            ),
            "cli": provided(
                "no_cli@messages are composed to an audience with a preview on the messaging "
                "screen; the CLI administers events only",
            ),
            "mcp": provided(
                "no_mcp@messages reach people and are sent only by organizers with a preview; "
                "an agent does not send them",
            ),
            "event_as_code": provided(
                "no_eac@messages are sent during the event to real people and are not "
                "configuration",
            ),
            "webhook": provided(
                "emit:message.sent=message.sent",
                "test:tests/integration/test_feature_webhook.py::test_each_audited_change_writes_the_outbox_event_its_claim_names",
            ),
            "archive": provided(
                "excluded@messages record who was written to and are not part of the archive "
                "contract",
                "test:tests/integration/test_feature_archive.py::test_each_excluded_model_is_in_the_archives_exclusion_list_and_not_in_its_contract",
            ),
            "analytics": provided(
                "no_analytics@messages are outbound communication and the summary does not "
                "count delivery",
            ),
            "privacy": provided(
                "erased:message_receipts",
                "person:sent_by=staff@the organizer who sent a message acts in their role and "
                "the message stays in the event history",
                "test:tests/integration/test_feature_privacy.py::test_a_real_subject_is_exported_and_erased_as_every_claim_says",
            ),
            "extension": provided(
                "hook:bulk_action=communications",
                "hook:approval_policy=communications",
                "hook:notification_category=communications",
                "test:tests/integration/test_feature_extension.py::test_every_hook_pair_is_claimed_once_and_the_manifests_agree_with_the_live_registries",
            ),
            "versioning": provided(
                "in_place@a sent message never changes; the audit trail records that it was sent",
            ),
            "fixtures": planned(
                "PD-S061-B02-T01",
                "The demo scenario creates no messages yet; its generator takes them in with "
                "the feature combinations.",
            ),
        },
        lifecycle=Lifecycle(
            "none",
            note=(
                "Created once when sent and never edited; "
                "recipients are rows beside it (MessageRecipient)."
            ),
        ),
    )
)
