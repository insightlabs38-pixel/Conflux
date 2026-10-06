"""Features of stages (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="stage",
        label="Stage",
        model="stages.Stage",
        claims={
            "identity": provided("field:public_id", "route:stage-detail"),
            "validation": provided(
                "check:stages.views.StageListView",
                "constraint:stages.Stage.unique_stage_name_event",
                "test:tests/integration/test_stage_builder_api.py::test_duplicate_stage_name_in_the_same_event_is_rejected",
            ),
            "authorization": provided(
                "route:stage-list",
                "route:stage-detail",
                "scope:event",
                "readers:members",
                "writers:admin,organizer",
                "test:tests/integration/test_stage_builder_api.py::test_non_organizer_cannot_create_a_stage",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
            ),
            "audit": provided(
                "write:stage-list:POST=stage.created",
                "write:stage-detail:PATCH=stage.updated",
                "write:stage-detail:DELETE=stage.deleted",
                "test:tests/integration/test_feature_audit.py::test_each_declared_change_records_its_audit_action",
                "test:tests/integration/test_feature_audit.py::test_a_refused_change_leaves_no_audit_row",
            ),
            "idempotency": provided(
                "mode:stage-list:POST=unique@stages.Stage.unique_stage_name_event",
                "mode:stage-detail:PATCH=natural",
                "mode:stage-detail:DELETE=natural",
                "test:tests/integration/test_feature_idempotency.py::test_a_repeated_change_does_what_its_declared_mode_says",
            ),
            "rest": provided(
                "list:stage-list",
                "no_detail@a stage is read in the event's ordered stage list",
                "paging:unpaged@bounded: an event has a handful of stages",
                "test:tests/integration/test_feature_rest.py::test_every_refusal_of_a_claimed_route_uses_the_shared_error_shape",
                "test:tests/integration/test_feature_rest.py::test_every_claimed_list_returns_what_its_schema_says",
            ),
            "sdk": provided(
                "generated:python",
                "generated:typescript",
                "test:tests/integration/test_feature_sdk.py::test_every_claimed_operation_works_through_the_generated_python_sdk",
            ),
            "search": provided(
                "no_query@read whole through its list: an event has a handful of stages, so a "
                "query over them is not offered",
            ),
            "ui_base": provided(
                "component:src/web/features/stage-builder/StageBuilder.tsx",
                "test:src/web/features/stage-builder/StageBuilder.test.tsx",
            ),
            "ui_advanced": provided(
                "uses:ConsequenceDialog@src/web/features/stage-builder/StageBuilder.tsx",
            ),
            "bulk": provided(
                "action:advance=stage.advanced",
                "test:tests/integration/test_bulk_operations.py::test_full_preview_apply_and_retry_are_atomic_and_audited",
            ),
            "cli": provided(
                "no_cli@stages are configured with the event and advanced through the bulk "
                "planner; the CLI administers events only",
            ),
            "mcp": provided(
                "tool:list_stages",
                "test:tests/integration/test_feature_mcp.py::test_each_claimed_tool_reaches_its_own_route_with_a_credential_limited_to_it",
            ),
            "event_as_code": provided(
                "section:stages",
                "section:stage_transitions",
                "test:tests/integration/test_event_as_code.py::test_document_applies_to_an_empty_event_and_reproduces_the_source",
                "test:tests/integration/test_feature_eac.py::test_every_section_writes_exactly_the_rows_it_declares",
            ),
            "webhook": provided(
                "emit:stage.created=stage.created",
                "emit:stage.deleted=stage.deleted",
                "emit:stage.updated=stage.updated",
                "test:tests/integration/test_feature_webhook.py::test_each_audited_change_writes_the_outbox_event_its_claim_names",
            ),
            "archive": provided(
                "table:stages.stage",
                "test:tests/integration/test_feature_archive.py::test_each_claimed_table_is_restored_with_its_rows",
            ),
        },
        lifecycle=Lifecycle(
            "none",
            note=(
                "Ordered by position, edited in place and deleted; "
                "its entries carry the state (StageEntry)."
            ),
        ),
    )
)
