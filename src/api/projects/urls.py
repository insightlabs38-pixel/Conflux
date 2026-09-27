from django.urls import path

from . import views

_prefix = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/projects/"

urlpatterns = [
    path(_prefix, views.ProjectListView.as_view(), name="project-list"),
    path(
        _prefix + "<uuid:project_public_id>/",
        views.ProjectDetailView.as_view(),
        name="project-detail",
    ),
    path(
        _prefix + "<uuid:project_public_id>/members/",
        views.ProjectMemberView.as_view(),
        name="project-members",
    ),
]
