from django.apps import AppConfig


class ArtifactsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "artifacts"

    def ready(self):
        from . import previews

        previews.register()
        from . import manifest  # noqa: F401 - declares what this app provides
