from django.urls import path

from .views import (
    FormDetailView,
    FormListView,
    FormPublishView,
    FormVersionListView,
    FormVersionRestoreView,
    ProjectFormListView,
    ProjectFormResponseView,
)

_prefix = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/forms/"
urlpatterns = [
    path(_prefix, FormListView.as_view(), name="form-list"),
    path(_prefix + "<uuid:form_public_id>/", FormDetailView.as_view(), name="form-detail"),
    path(
        _prefix + "<uuid:form_public_id>/versions/",
        FormVersionListView.as_view(),
        name="form-version-list",
    ),
    path(
        _prefix + "<uuid:form_public_id>/publish/", FormPublishView.as_view(), name="form-publish"
    ),
    path(
        _prefix + "<uuid:form_public_id>/versions/<uuid:version_public_id>/restore/",
        FormVersionRestoreView.as_view(),
        name="form-version-restore",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/projects/<uuid:project_public_id>/forms/",
        ProjectFormListView.as_view(),
        name="project-form-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/projects/<uuid:project_public_id>/forms/<uuid:version_public_id>/response/",
        ProjectFormResponseView.as_view(),
        name="project-form-response",
    ),
]
