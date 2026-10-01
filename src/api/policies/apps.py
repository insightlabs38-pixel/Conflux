from django.apps import AppConfig


class PoliciesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "policies"

    def ready(self):
        from . import manifest  # noqa: F401 - declares what this app provides
