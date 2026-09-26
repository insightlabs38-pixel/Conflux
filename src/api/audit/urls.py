from django.urls import path

from . import views

urlpatterns = [
    path(
        "<uuid:workspace_public_id>/",
        views.WorkspaceAuditLogView.as_view(),
        name="workspace-audit-log",
    ),
]
