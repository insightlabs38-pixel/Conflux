"""Features of awards (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="award",
        label="Award",
        model="awards.Award",
        claims={"identity": provided("field:public_id", "route:award-publish")},
        lifecycle=Lifecycle(
            "timestamp",
            field="published_at",
            states=(("draft", "Draft"), ("published", "Published")),
            initial=("draft",),
            transitions={"draft": ("published",)},
            terminal=("published",),
            via=("awards.views.AwardPublishView",),
        ),
    )
)
