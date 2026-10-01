"""Features of stages (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="stage",
        label="Stage",
        model="stages.Stage",
        claims={"identity": provided("field:public_id", "route:stage-detail")},
        lifecycle=Lifecycle(
            "none",
            note=(
                "Ordered by position, edited in place and deleted; "
                "its entries carry the state (StageEntry)."
            ),
        ),
    )
)
