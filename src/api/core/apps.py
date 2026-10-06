from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        from . import (  # noqa: F401 - platform capabilities and the startup check
            checks,
            features_audit,
            features_authorization,
            features_idempotency,
            features_identity,
            features_rest,
            features_sdk,
            features_search,
            features_ui,
            features_validation,
            manifest_core,
        )
