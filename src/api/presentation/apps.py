from django.apps import AppConfig


class PresentationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "presentation"

    def ready(self):
        from . import manifest, preview  # noqa: F401 - manifest declares what this app provides

        preview.register()
