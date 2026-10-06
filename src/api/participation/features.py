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
            "authorization": provided(
                "route:my-team",
                "route:my-team-leave",
                "route:my-team-transfer-captain",
                "route:my-team-invite-list",
                "route:team-invite-redeem",
                "scope:event",
                "readers:members",
                "writers:members",
                "own:team_member",
                "test:tests/integration/test_team_lifecycle.py::test_only_the_captain_can_transfer_captaincy",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_a_non_member_of_a_project_can_never_change_it_or_what_hangs_off_it",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
            ),
        },
        lifecycle=Lifecycle(
            "none",
            note="Edited in place; joining and leaving are membership rows (TeamMembership).",
        ),
    )
)
