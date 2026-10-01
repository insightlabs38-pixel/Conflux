from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "projects"

    def ready(self):
        from . import threads  # noqa: F401 - registers the project notes subject
