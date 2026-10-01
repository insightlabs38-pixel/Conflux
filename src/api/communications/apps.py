from django.apps import AppConfig


class CommunicationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "communications"

    def ready(self):
        from . import (  # noqa: F401 - policy, categories, notifier
            approvals,
            manifest,  # noqa: F401 - declares what this app provides
            notifications,
            threads,
        )
