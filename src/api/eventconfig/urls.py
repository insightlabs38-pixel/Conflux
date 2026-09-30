from django.urls import path

from . import views

_WORKSPACE = "workspaces/<uuid:workspace_public_id>"

urlpatterns = [
    path(f"{_WORKSPACE}/modules/", views.WorkspaceModulesView.as_view(), name="workspace-modules"),
    path(
        f"{_WORKSPACE}/events/<uuid:event_public_id>/configuration/",
        views.EventConfigurationView.as_view(),
        name="event-configuration",
    ),
    path(
        f"{_WORKSPACE}/events/<uuid:event_public_id>/configuration/generated/",
        views.EventGeneratedConfigurationView.as_view(),
        name="event-generated-configuration",
    ),
    path(
        f"{_WORKSPACE}/events/<uuid:event_public_id>/workflow/",
        views.EventWorkflowView.as_view(),
        name="event-workflow",
    ),
    path(
        f"{_WORKSPACE}/events/<uuid:event_public_id>/readiness/",
        views.EventReadinessView.as_view(),
        name="event-readiness",
    ),
    path(
        f"{_WORKSPACE}/events/<uuid:event_public_id>/modules/<slug:module_key>/",
        views.EventModuleView.as_view(),
        name="event-module",
    ),
]
