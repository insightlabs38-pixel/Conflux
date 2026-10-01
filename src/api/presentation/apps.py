from django.apps import AppConfig


class PresentationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "presentation"

    def ready(self):
        from . import manifest  # noqa: F401 - declares what this app provides
