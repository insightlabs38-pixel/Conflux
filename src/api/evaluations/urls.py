from django.urls import path

from . import views

_STAGE = (
    "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>"
    "/stages/<uuid:stage_public_id>"
)

urlpatterns = [
    path(
        f"{_STAGE}/evaluation-plans/",
        views.EvaluationPlanListView.as_view(),
        name="evaluation-plan-list",
    ),
    path(
        f"{_STAGE}/evaluation-plans/<uuid:plan_public_id>/",
        views.EvaluationPlanDetailView.as_view(),
        name="evaluation-plan-detail",
    ),
    path(
        f"{_STAGE}/evaluation-plans/<uuid:plan_public_id>/publish-rubric/",
        views.RubricPublishView.as_view(),
        name="evaluation-plan-publish-rubric",
    ),
    path(
        f"{_STAGE}/evaluation-plans/<uuid:plan_public_id>/ballots/",
        views.BallotListCreateView.as_view(),
        name="evaluation-plan-ballots",
    ),
]
