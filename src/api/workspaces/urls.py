from django.urls import path

from . import views

urlpatterns = [
    path("", views.WorkspaceCreateView.as_view(), name="workspace-create"),
    path(
        "<uuid:workspace_public_id>/members/",
        views.WorkspaceMembersView.as_view(),
        name="workspace-members",
    ),
]
