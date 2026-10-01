from django.apps import AppConfig


class FormsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "forms"

    def ready(self):
        from . import versions

        versions.register()
        from . import manifest  # noqa: F401 - declares what this app provides
