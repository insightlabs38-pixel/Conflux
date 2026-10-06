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
            "audit": provided(
                "write:webhook-list:POST=webhook.created",
                "write:webhook-detail:PATCH=webhook.updated",
                "test:tests/integration/test_feature_audit.py::test_each_declared_change_records_its_audit_action",
                "test:tests/integration/test_feature_audit.py::test_a_refused_change_leaves_no_audit_row",
            ),
            "idempotency": provided(
                "mode:webhook-list:POST=none@a new subscription is made each time and its "
                "response carries the signing secret, which a replayed response would have to "
                "store",
                "mode:webhook-detail:PATCH=natural",
                "test:tests/integration/test_feature_idempotency.py::test_a_repeated_change_does_what_its_declared_mode_says",
            ),
            "rest": provided(
                "list:webhook-list",
                "no_detail@a subscription is read in the workspace list; its secret is shown once  "
                "at creation",
                "paging:unpaged@bounded: a workspace has a few subscriptions",
                "test:tests/integration/test_feature_rest.py::test_every_refusal_of_a_claimed_route_uses_the_shared_error_shape",
                "test:tests/integration/test_feature_rest.py::test_every_claimed_list_returns_what_its_schema_says",
            ),
            "sdk": provided(
                "generated:python",
                "generated:typescript",
                "test:tests/integration/test_feature_sdk.py::test_every_claimed_operation_works_through_the_generated_python_sdk",
            ),
            "search": provided(
                "no_query@read whole through its list: a workspace has a few subscriptions, so a "
                "query over them is not offered",
            ),
            "ui_base": provided(
                "component:src/web/features/integrations/WebhooksPanel.tsx",
                "test:src/web/features/integrations/WebhooksPanel.test.tsx",
            ),
            "ui_advanced": provided(
                "no_advanced@a subscription is a URL, a set of event types and a switch, all in "
                "the base screen",
            ),
            "bulk": provided(
                "no_bulk@a subscription is an integration an admin sets up one at a time with "
                "its own secret",
            ),
            "cli": provided(
                "no_cli@a subscription's secret is shown once and is set up in the web or API, "
                "not typed in a shell",
            ),
            "mcp": provided(
                "no_mcp@a subscription holds a secret shown once and is set up by an admin, "
                "never through an agent",
            ),
            "event_as_code": provided(
                "no_eac@a subscription holds a secret that must never be exported in a document",
            ),
            "webhook": provided(
                "silent:webhook.created@a subscription must not announce its own setup or "
                "secret to other subscribers",
                "silent:webhook.updated@a subscription must not announce its own setup or "
                "secret to other subscribers",
                "test:tests/integration/test_feature_webhook.py::test_each_audited_change_writes_the_outbox_event_its_claim_names",
            ),
            "archive": provided(
                "excluded@a subscription holds a signing secret and a target URL of the old "
                "event's integration",
                "test:tests/integration/test_feature_archive.py::test_each_excluded_model_is_in_the_archives_exclusion_list_and_not_in_its_contract",
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
