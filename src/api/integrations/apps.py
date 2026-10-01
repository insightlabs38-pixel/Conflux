from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "integrations"

    def ready(self):
        from . import (
            jobs,  # noqa: F401 - registers this app's background job kinds
            manifest,  # noqa: F401 - declares what this app provides
        )
