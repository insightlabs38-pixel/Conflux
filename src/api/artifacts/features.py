"""Features of artifacts (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="artifact",
        label="Artifact",
        model="artifacts.Artifact",
        claims={
            "identity": provided("field:public_id", "route:artifact-detail"),
            "validation": provided(
                "check:artifacts.models.Artifact.clean",
                "check:artifacts.validators.validate_artifact",
                "test:tests/integration/test_artifact_api.py::test_external_artifact_api_rejects_bad_url_and_nonmember",
            ),
        },
        lifecycle=Lifecycle(
            "choice",
            field="status",
            initial=("pending", "uploaded"),
            transitions={
                "pending": ("uploaded", "ready", "rejected", "purged"),
                "uploaded": ("ready", "rejected", "purged"),
                "ready": ("rejected", "purged"),
                "rejected": ("ready", "purged"),
            },
            terminal=("purged",),
            via=(
                "artifacts.services.complete_upload",
                "artifacts.validators.validate_artifact",
                "integrations.privacy.enforce_retention",
            ),
        ),
    )
)
