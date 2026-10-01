"""Features of artifacts (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="artifact",
        label="Artifact",
        model="artifacts.Artifact",
        claims={"identity": provided("field:public_id", "route:artifact-detail")},
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
