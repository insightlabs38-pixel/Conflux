"""Features of participation (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="team",
        label="Team",
        model="participation.Team",
        claims={"identity": provided("field:public_id")},
        lifecycle=Lifecycle(
            "none",
            note="Edited in place; joining and leaving are membership rows (TeamMembership).",
        ),
    )
)
