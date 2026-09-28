from django.urls import path

from . import views

_e = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/"
_p = _e + "projects/<uuid:project_public_id>/continuation/"

urlpatterns = [
    path(_p, views.ProjectContinuationView.as_view(), name="project-continuation"),
    path(_p + "updates/", views.ContinuationUpdateView.as_view(), name="continuation-updates"),
    path(
        _p + "hide/",
        views.ContinuationModerationView.as_view(hide=True),
        name="continuation-hide",
    ),
    path(
        _p + "restore/",
        views.ContinuationModerationView.as_view(hide=False),
        name="continuation-restore",
    ),
    path(
        _e + "continuations/", views.OrganizerContinuationListView.as_view(), name="continuations"
    ),
    path(
        "events/<uuid:event_public_id>/continuations/",
        views.PublicContinuationListView.as_view(),
        name="public-continuations",
    ),
]
