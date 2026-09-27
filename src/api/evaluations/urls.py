from django.urls import path

from . import views

_EVENT = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>"
_STAGE = f"{_EVENT}/stages/<uuid:stage_public_id>"
_POOL = f"{_EVENT}/evaluation-pools/<uuid:pool_public_id>"
_PLAN = f"{_STAGE}/evaluation-plans/<uuid:plan_public_id>"

urlpatterns = [
    path(
        f"{_STAGE}/evaluation-plans/",
        views.EvaluationPlanListView.as_view(),
        name="evaluation-plan-list",
    ),
    path(f"{_PLAN}/", views.EvaluationPlanDetailView.as_view(), name="evaluation-plan-detail"),
    path(
        f"{_PLAN}/publish-rubric/",
        views.RubricPublishView.as_view(),
        name="evaluation-plan-publish-rubric",
    ),
    path(f"{_PLAN}/ballots/", views.BallotListCreateView.as_view(), name="evaluation-plan-ballots"),
    path(
        f"{_PLAN}/assignments/activate/",
        views.AssignmentActivateView.as_view(),
        name="evaluation-plan-assignments-activate",
    ),
    path(
        f"{_PLAN}/assignments/",
        views.AssignmentDetailView.as_view(),
        name="evaluation-plan-assignments",
    ),
    path(
        f"{_EVENT}/evaluation-pools/",
        views.EvaluationPoolListView.as_view(),
        name="evaluation-pool-list",
    ),
    path(
        f"{_POOL}/memberships/",
        views.PoolMembershipListView.as_view(),
        name="pool-membership-list",
    ),
    path(
        f"{_POOL}/memberships/<uuid:membership_public_id>/",
        views.PoolMembershipDetailView.as_view(),
        name="pool-membership-detail",
    ),
    path(
        f"{_EVENT}/judge-conflicts/",
        views.ConflictOfInterestListCreateView.as_view(),
        name="judge-conflict-list",
    ),
    path(
        f"{_PLAN}/normalization-runs/",
        views.NormalizationRunListView.as_view(),
        name="evaluation-plan-normalization-runs",
    ),
]
