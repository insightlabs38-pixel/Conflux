from django.apps import AppConfig


class EvaluationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "evaluations"

    def ready(self):
        from . import versions

        versions.register()
        from . import manifest  # noqa: F401 - declares what this app provides
