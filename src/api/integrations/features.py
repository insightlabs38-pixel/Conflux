"""Features of integrations (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="webhook",
        label="Webhook subscription",
        model="integrations.WebhookSubscription",
        claims={"identity": provided("field:public_id", "route:webhook-detail")},
        lifecycle=Lifecycle(
            "flag",
            field="enabled",
            states=(("disabled", "Disabled"), ("enabled", "Enabled")),
            initial=("enabled",),
            transitions={"enabled": ("disabled",), "disabled": ("enabled",)},
            via=("integrations.webhook_views.WebhookSubscriptionView",),
        ),
    )
)
