from django.urls import path

from . import views

urlpatterns = [
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/stages/",
        views.StageListView.as_view(),
        name="stage-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/stages/<uuid:stage_public_id>/",
        views.StageDetailView.as_view(),
        name="stage-detail",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/stage-transitions/",
        views.StageTransitionListView.as_view(),
        name="stage-transition-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/stage-transitions/<uuid:transition_public_id>/",
        views.StageTransitionDetailView.as_view(),
        name="stage-transition-detail",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/stage-graph/validate/",
        views.GraphValidationView.as_view(),
        name="stage-graph-validate",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/stages/<uuid:stage_public_id>/advance/",
        views.StageAdvancementView.as_view(),
        name="stage-advance",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/stage-evidence/",
        views.StageEvidenceView.as_view(),
        name="stage-evidence",
    ),
]
