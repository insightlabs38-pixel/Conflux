from django.urls import path

from .views import McpEndpointView

urlpatterns = [
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/mcp/",
        McpEndpointView.as_view(),
        name="mcp-endpoint",
    )
]
