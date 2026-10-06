from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        from . import (  # noqa: F401 - platform capabilities and the startup check
            checks,
            features_analytics,
            features_archive,
            features_audit,
            features_authorization,
            features_bulk,
            features_cli,
            features_eac,
            features_extension,
            features_fixtures,
            features_idempotency,
            features_identity,
            features_mcp,
            features_privacy,
            features_rest,
            features_sdk,
            features_search,
            features_ui,
            features_validation,
            features_versioning,
            features_webhook,
            manifest_core,
        )
