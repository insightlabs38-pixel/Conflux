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
