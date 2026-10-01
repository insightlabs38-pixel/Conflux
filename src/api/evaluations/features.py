"""Features of judging (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="evaluation_plan",
        label="Evaluation plan",
        model="evaluations.EvaluationPlan",
        claims={"identity": provided("field:public_id", "route:evaluation-plan-detail")},
        lifecycle=Lifecycle(
            "none",
            note=(
                "Configured in place; its rubric is published as an immutable RubricVersion "
                "and results through normalization runs."
            ),
        ),
    )
)
