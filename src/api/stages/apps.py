from django.apps import AppConfig


class StagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "stages"

    def ready(self):
        from . import manifest  # noqa: F401 - declares what this app provides
