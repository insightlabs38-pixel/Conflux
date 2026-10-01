"""Features of forms (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="form",
        label="Form",
        model="forms.FormDefinition",
        claims={"identity": provided("field:public_id", "route:form-detail")},
        lifecycle=Lifecycle(
            "none",
            note="A draft edited in place; publishing makes an immutable numbered FormVersion.",
        ),
    )
)
