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
