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
            "audit": provided(
                "write:evaluation-plan-list:POST=evaluation_plan.created",
                "write:evaluation-plan-detail:PATCH=evaluation_plan.updated",
                "write:evaluation-plan-detail:DELETE=evaluation_plan.deleted",
                "test:tests/integration/test_feature_audit.py::test_each_declared_change_records_its_audit_action",
                "test:tests/integration/test_feature_audit.py::test_a_refused_change_leaves_no_audit_row",
            ),
            "idempotency": provided(
                "mode:evaluation-plan-list:POST=unique@evaluations.EvaluationPlan.unique_evaluation_plan_name",
                "mode:evaluation-plan-detail:PATCH=natural",
                "mode:evaluation-plan-detail:DELETE=natural",
                "test:tests/integration/test_feature_idempotency.py::test_a_repeated_change_does_what_its_declared_mode_says",
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
