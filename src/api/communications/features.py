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
