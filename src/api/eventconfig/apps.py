from django.apps import AppConfig


class EventconfigConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "eventconfig"

    def ready(self):
        from . import timeline  # noqa: F401 - registers what each domain puts on the timeline
