"""Features of stages (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="stage",
        label="Stage",
        model="stages.Stage",
        claims={
            "identity": provided("field:public_id", "route:stage-detail"),
            "validation": provided(
                "check:stages.views.StageListView",
                "constraint:stages.Stage.unique_stage_name_event",
                "test:tests/integration/test_stage_builder_api.py::test_duplicate_stage_name_in_the_same_event_is_rejected",
            ),
            "authorization": provided(
                "route:stage-list",
                "route:stage-detail",
                "scope:event",
                "readers:members",
                "writers:admin,organizer",
                "test:tests/integration/test_stage_builder_api.py::test_non_organizer_cannot_create_a_stage",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
            ),
            "audit": provided(
                "write:stage-list:POST=stage.created",
                "write:stage-detail:PATCH=stage.updated",
                "write:stage-detail:DELETE=stage.deleted",
                "test:tests/integration/test_feature_audit.py::test_each_declared_change_records_its_audit_action",
                "test:tests/integration/test_feature_audit.py::test_a_refused_change_leaves_no_audit_row",
            ),
            "idempotency": provided(
                "mode:stage-list:POST=unique@stages.Stage.unique_stage_name_event",
                "mode:stage-detail:PATCH=natural",
                "mode:stage-detail:DELETE=natural",
                "test:tests/integration/test_feature_idempotency.py::test_a_repeated_change_does_what_its_declared_mode_says",
            ),
            "rest": provided(
                "list:stage-list",
                "no_detail@a stage is read in the event's ordered stage list",
                "paging:unpaged@bounded: an event has a handful of stages",
                "test:tests/integration/test_feature_rest.py::test_every_refusal_of_a_claimed_route_uses_the_shared_error_shape",
                "test:tests/integration/test_feature_rest.py::test_every_claimed_list_returns_what_its_schema_says",
            ),
            "sdk": provided(
                "generated:python",
                "generated:typescript",
                "test:tests/integration/test_feature_sdk.py::test_every_claimed_operation_works_through_the_generated_python_sdk",
            ),
            "search": provided(
                "no_query@read whole through its list: an event has a handful of stages, so a "
                "query over them is not offered",
            ),
        },
        lifecycle=Lifecycle(
            "none",
            note=(
                "Ordered by position, edited in place and deleted; "
                "its entries carry the state (StageEntry)."
            ),
        ),
    )
)
