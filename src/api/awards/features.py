"""Features of awards (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="award",
        label="Award",
        model="awards.Award",
        claims={
            "identity": provided("field:public_id", "route:award-publish"),
            "validation": provided(
                "check:awards.models.Award.clean",
                "constraint:awards.Award.award_winner_count_positive",
                "test:tests/integration/test_award_api.py::test_cross_event_and_invalid_component_are_rejected",
            ),
            "authorization": provided(
                "route:award-list",
                "route:award-publish",
                "scope:event",
                "readers:admin,organizer",
                "writers:admin,organizer",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
            ),
            "audit": provided(
                "write:award-list:POST=award.created",
                "write:award-publish:POST=award.published",
                "test:tests/integration/test_feature_audit.py::test_each_declared_change_records_its_audit_action",
                "test:tests/integration/test_feature_audit.py::test_a_refused_change_leaves_no_audit_row",
            ),
            "idempotency": provided(
                "mode:award-list:POST=unique@awards.Award.unique_award_name_event",
                "mode:award-publish:POST=locked@awards.views.AwardPublishView.post",
                "test:tests/integration/test_feature_idempotency.py::test_a_repeated_change_does_what_its_declared_mode_says",
            ),
            "rest": provided(
                "list:award-list",
                "no_detail@an award is read in the event's award list with its winners",
                "paging:unpaged@bounded: an event has tens of awards",
                "test:tests/integration/test_feature_rest.py::test_every_refusal_of_a_claimed_route_uses_the_shared_error_shape",
                "test:tests/integration/test_feature_rest.py::test_every_claimed_list_returns_what_its_schema_says",
            ),
            "sdk": provided(
                "generated:python",
                "generated:typescript",
                "test:tests/integration/test_feature_sdk.py::test_every_claimed_operation_works_through_the_generated_python_sdk",
            ),
            "search": provided(
                "no_query@read whole through its list: an event has tens of awards, so a query "
                "over them is not offered",
            ),
        },
        lifecycle=Lifecycle(
            "timestamp",
            field="published_at",
            states=(("draft", "Draft"), ("published", "Published")),
            initial=("draft",),
            transitions={"draft": ("published",)},
            terminal=("published",),
            via=("awards.views.AwardPublishView",),
        ),
    )
)
