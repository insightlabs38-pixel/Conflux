"""Features of integrations (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="webhook",
        label="Webhook subscription",
        model="integrations.WebhookSubscription",
        claims={
            "identity": provided("field:public_id", "route:webhook-detail"),
            "validation": provided(
                "check:integrations.webhooks.validate_destination",
                "test:tests/integration/test_webhooks.py::test_unsafe_destination_is_rejected_at_creation_and_delivery",
            ),
            "authorization": provided(
                "route:webhook-list",
                "route:webhook-detail",
                "scope:workspace",
                "readers:admin,organizer",
                "writers:admin,organizer",
                "test:tests/integration/test_webhooks.py::test_subscription_is_scoped_and_secret_is_one_time",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
            ),
        },
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
