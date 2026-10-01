"""Features of participation (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="team",
        label="Team",
        model="participation.Team",
        claims={
            "identity": provided("field:public_id"),
            "validation": provided(
                "check:participation.services.join_team",
                "constraint:participation.Team.unique_team_name_event",
                "test:tests/integration/test_team_lifecycle.py::test_a_team_cannot_exceed_the_maximum_size",
            ),
        },
        lifecycle=Lifecycle(
            "none",
            note="Edited in place; joining and leaving are membership rows (TeamMembership).",
        ),
    )
)
