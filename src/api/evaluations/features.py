"""Features of judging (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="evaluation_plan",
        label="Evaluation plan",
        model="evaluations.EvaluationPlan",
        claims={
            "identity": provided("field:public_id", "route:evaluation-plan-detail"),
            "validation": provided(
                "check:evaluations.models.EvaluationPlan.clean",
                "check:evaluations.rubric.clean_criteria",
                "constraint:evaluations.EvaluationPlan.unique_evaluation_plan_name",
                "test:tests/integration/test_evaluation_api.py::test_rubric_validation_rejects_bad_weights_and_ranges",
            ),
            "authorization": provided(
                "route:evaluation-plan-list",
                "route:evaluation-plan-detail",
                "scope:event",
                "readers:members",
                "writers:admin,organizer",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
            ),
        },
        lifecycle=Lifecycle(
            "none",
            note=(
                "Configured in place; its rubric is published as an immutable RubricVersion "
                "and results through normalization runs."
            ),
        ),
    )
)
