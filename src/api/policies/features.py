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
        },
        lifecycle=Lifecycle(
            "none",
            note="Edited in place and deleted; evaluation reads the stored rules at call time.",
        ),
    )
)
