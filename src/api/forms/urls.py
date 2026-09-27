from django.urls import path

from .views import ProjectFormResponseView

urlpatterns = [
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/projects/<uuid:project_public_id>/forms/<uuid:version_public_id>/response/",
        ProjectFormResponseView.as_view(),
        name="project-form-response",
    ),
]
