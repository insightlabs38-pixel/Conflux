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
        },
        lifecycle=Lifecycle(
            "none",
            note="A draft edited in place; publishing makes an immutable numbered FormVersion.",
        ),
    )
)
