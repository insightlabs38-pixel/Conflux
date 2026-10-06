"""Features of policies (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="policy",
        label="Policy",
        model="policies.Policy",
        claims={
            "identity": provided("field:public_id", "route:policy-detail"),
            "validation": provided(
                "check:policies.models.Policy.clean",
                "check:policies.evaluator.validate_structure",
                "constraint:policies.Policy.unique_policy_name_event",
                "test:tests/integration/test_policy_bindings.py::test_a_malformed_ast_is_rejected_at_save_time",
            ),
            "authorization": provided(
                "route:policy-list",
                "route:policy-detail",
                "scope:event",
                "readers:admin,organizer",
                "writers:admin,organizer",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
            ),
        },
        lifecycle=Lifecycle(
            "none",
            note="Edited in place and deleted; evaluation reads the stored rules at call time.",
        ),
    )
)
