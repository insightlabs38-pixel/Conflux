from django.urls import path

from . import views

urlpatterns = [
    path(
        "<uuid:workspace_public_id>/",
        views.WorkspaceAuditLogView.as_view(),
        name="workspace-audit-log",
    ),
    path(
        "<uuid:workspace_public_id>/events/<uuid:event_public_id>/config-history/",
        views.EventConfigHistoryView.as_view(),
        name="event-config-history",
    ),
]
