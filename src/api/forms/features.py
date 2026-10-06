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
        },
        lifecycle=Lifecycle(
            "none",
            note="A draft edited in place; publishing makes an immutable numbered FormVersion.",
        ),
    )
)
