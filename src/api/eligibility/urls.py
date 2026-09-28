from django.urls import path

from . import views

_event = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/"
_project = _event + "projects/<uuid:project_public_id>/eligibility/"

urlpatterns = [
    path(_event + "eligibility-rules/", views.RulesView.as_view(), name="eligibility-rules"),
    path(
        _event + "eligibility-reviews/", views.ReviewListView.as_view(), name="eligibility-reviews"
    ),
    path(_project, views.ProjectEligibilityView.as_view(), name="project-eligibility"),
    path(_project + "checks/", views.RunChecksView.as_view(), name="eligibility-checks"),
    path(
        _project + "findings/", views.RaiseFindingView.as_view(), name="eligibility-finding-raise"
    ),
    path(
        _project + "findings/<uuid:finding_public_id>/close/",
        views.CloseFindingView.as_view(),
        name="eligibility-finding-close",
    ),
    path(
        _project + "findings/<uuid:finding_public_id>/respond/",
        views.RespondView.as_view(),
        name="eligibility-finding-respond",
    ),
    path(_project + "decision/", views.DecisionView.as_view(), name="eligibility-decision"),
]
