from django.urls import path

from . import views

_prefix = (
    "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/"
    "projects/<uuid:project_public_id>/artifacts/"
)

urlpatterns = [
    path(_prefix, views.ArtifactListView.as_view(), name="artifact-list"),
    path(
        _prefix + "upload-intents/", views.UploadIntentView.as_view(), name="artifact-upload-intent"
    ),
    path(
        _prefix + "<uuid:artifact_public_id>/",
        views.ArtifactDetailView.as_view(),
        name="artifact-detail",
    ),
    path(
        _prefix + "<uuid:artifact_public_id>/upload-intents/<uuid:intent_public_id>/complete/",
        views.UploadCompleteView.as_view(),
        name="artifact-upload-complete",
    ),
]
