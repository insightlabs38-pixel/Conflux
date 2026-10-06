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
