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
    path(
        _prefix + "<uuid:project_public_id>/submissions/",
        views.SubmissionStageListView.as_view(),
        name="submission-stage-list",
    ),
    path(
        _prefix + "<uuid:project_public_id>/submissions/<uuid:stage_public_id>/",
        views.SubmissionDetailView.as_view(),
        name="submission-detail",
    ),
    path(
        _prefix + "<uuid:project_public_id>/submissions/<uuid:stage_public_id>/finalize/",
        views.SubmissionFinalizeView.as_view(),
        name="submission-finalize",
    ),
    path(
        _prefix + "<uuid:project_public_id>/submissions/<uuid:stage_public_id>/reopen/",
        views.SubmissionReopenView.as_view(),
        name="submission-reopen",
    ),
    path(
        _prefix + "<uuid:project_public_id>/submissions/<uuid:stage_public_id>/diff/",
        views.SubmissionDiffView.as_view(),
        name="submission-diff",
    ),
]
