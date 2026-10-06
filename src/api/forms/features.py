"""Features of forms (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="form",
        label="Form",
        model="forms.FormDefinition",
        claims={
            "identity": provided("field:public_id", "route:form-detail"),
            "validation": provided(
                "check:forms.models.FormDefinition.clean",
                "check:forms.validation.validate_schema",
                "constraint:forms.FormDefinition.unique_form_name_event",
                "test:tests/integration/test_form_versions.py::test_form_rejects_cross_event_stage_and_duplicate_field_ids",
            ),
            "authorization": provided(
                "route:form-list",
                "route:form-detail",
                "scope:event",
                "readers:admin,organizer",
                "writers:admin,organizer",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
            ),
            "audit": provided(
                "write:form-list:POST=form.created",
                "write:form-detail:PUT=form.draft_saved",
                "test:tests/integration/test_feature_audit.py::test_each_declared_change_records_its_audit_action",
                "test:tests/integration/test_feature_audit.py::test_a_refused_change_leaves_no_audit_row",
            ),
            "idempotency": provided(
                "mode:form-list:POST=unique@forms.FormDefinition.unique_form_name_event",
                "mode:form-detail:PUT=natural",
                "test:tests/integration/test_feature_idempotency.py::test_a_repeated_change_does_what_its_declared_mode_says",
            ),
            "rest": provided(
                "list:form-list",
                "detail:form-detail",
                "paging:unpaged@bounded: an event has a handful of forms",
                "test:tests/integration/test_feature_rest.py::test_every_refusal_of_a_claimed_route_uses_the_shared_error_shape",
                "test:tests/integration/test_feature_rest.py::test_every_claimed_list_returns_what_its_schema_says",
            ),
            "sdk": provided(
                "generated:python",
                "generated:typescript",
                "test:tests/integration/test_feature_sdk.py::test_every_claimed_operation_works_through_the_generated_python_sdk",
            ),
            "search": provided(
                "no_query@read whole through its list: an event has a handful of forms, so a "
                "query over them is not offered",
            ),
            "ui_base": provided(
                "component:src/web/features/form-builder/FormBuilder.tsx",
                "test:src/web/features/form-builder/FormBuilder.test.tsx",
            ),
            "ui_advanced": provided(
                "uses:VersionCompare@src/web/features/form-builder/FormBuilder.tsx",
                "uses:PreviewBar@src/web/features/form-builder/FormPreviewAs.tsx",
            ),
            "bulk": provided(
                "no_bulk@a form is built and versioned one at a time, and its versions are "
                "compared, not batched",
            ),
        },
        lifecycle=Lifecycle(
            "none",
            note="A draft edited in place; publishing makes an immutable numbered FormVersion.",
        ),
    )
)
