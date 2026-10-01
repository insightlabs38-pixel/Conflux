from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        from . import (  # noqa: F401 - platform capabilities and the startup check
            checks,
            features_identity,
            manifest_core,
        )
