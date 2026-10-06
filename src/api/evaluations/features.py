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
            "rest": provided(
                "list:evaluation-plan-list",
                "detail:evaluation-plan-detail",
                "paging:unpaged@bounded: a stage has one or two plans",
                "test:tests/integration/test_feature_rest.py::test_every_refusal_of_a_claimed_route_uses_the_shared_error_shape",
                "test:tests/integration/test_feature_rest.py::test_every_claimed_list_returns_what_its_schema_says",
            ),
            "sdk": provided(
                "generated:python",
                "generated:typescript",
                "test:tests/integration/test_feature_sdk.py::test_every_claimed_operation_works_through_the_generated_python_sdk",
            ),
            "search": provided(
                "no_query@read whole through its list: a stage has one or two plans, so a query "
                "over them is not offered",
            ),
            "ui_base": provided(
                "component:src/web/features/judging/EvaluationBuilder.tsx",
                "test:src/web/features/judging/EvaluationBuilder.test.tsx",
            ),
            "ui_advanced": provided(
                "no_advanced@the rubric is edited in the base screen; its advanced views "
                "(progress, results) belong to the judging feature",
            ),
            "bulk": provided(
                "action:assign=assignment.activated",
                "test:tests/integration/test_bulk_operations.py::test_full_preview_apply_and_retry_are_atomic_and_audited",
            ),
            "cli": provided(
                "no_cli@evaluation plans are built and activated on the judging screens; the "
                "CLI administers events only",
            ),
            "mcp": provided(
                "no_mcp@plan progress and results are offered as read tools over routes not yet "
                "claimed by this feature",
            ),
            "event_as_code": provided(
                "section:evaluation_plans",
                "test:tests/integration/test_event_as_code.py::test_document_applies_to_an_empty_event_and_reproduces_the_source",
                "test:tests/integration/test_feature_eac.py::test_every_section_writes_exactly_the_rows_it_declares",
            ),
            "webhook": provided(
                "silent:evaluation_plan.created@judging plans are internal configuration; "
                "subscribers learn of results when published",
                "silent:evaluation_plan.deleted@judging plans are internal configuration; "
                "subscribers learn of results when published",
                "silent:evaluation_plan.updated@judging plans are internal configuration; "
                "subscribers learn of results when published",
                "test:tests/integration/test_feature_webhook.py::test_each_audited_change_writes_the_outbox_event_its_claim_names",
            ),
            "archive": provided(
                "table:evaluations.evaluationplan",
                "test:tests/integration/test_feature_archive.py::test_each_claimed_table_is_restored_with_its_rows",
            ),
            "analytics": provided(
                "section:judging",
                "measure:judging.plan_count",
                "measure:judging.plans",
                "test:tests/integration/test_feature_analytics.py::test_every_claimed_measure_and_breakdown_is_in_the_summary_of_a_real_event",
            ),
            "privacy": provided(
                "retained:ballots",
                "retained:assignments",
                "retained:pairwise_comparisons",
                "test:tests/integration/test_feature_privacy.py::test_a_real_subject_is_exported_and_erased_as_every_claim_says",
            ),
            "extension": provided(
                "hook:assignment_strategy=evaluations",
                "hook:version_source=evaluations",
                "test:tests/integration/test_feature_extension.py::test_every_hook_pair_is_claimed_once_and_the_manifests_agree_with_the_live_registries",
            ),
            "versioning": provided(
                "immutable:evaluations.RubricVersion",
                "immutable:evaluations.AssignmentVersion",
                "immutable:evaluations.NormalizationRun",
                "immutable:evaluations.PairwiseRun",
                "diff:rubric",
                "test:tests/integration/test_feature_versioning.py::test_each_claimed_version_model_refuses_an_edit_and_a_delete",
            ),
            "fixtures": provided(
                "seeded:hackathon",
                "test:tests/integration/test_feature_fixtures.py::test_the_demo_scenario_creates_exactly_the_features_the_claims_say",
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
