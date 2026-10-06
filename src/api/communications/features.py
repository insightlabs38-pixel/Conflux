"""Features of communications (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

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
