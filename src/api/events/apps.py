from django.apps import AppConfig


class EventsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "events"

    def ready(self):
        from . import (
            manifest,  # noqa: F401 - declares what this app provides
            threads,  # noqa: F401 - registers the application notes subject
        )
