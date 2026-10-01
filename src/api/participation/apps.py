from django.apps import AppConfig


class ParticipationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "participation"

    def ready(self):
        from . import manifest  # noqa: F401 - declares what this app provides
