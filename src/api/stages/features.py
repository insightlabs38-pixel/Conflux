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
