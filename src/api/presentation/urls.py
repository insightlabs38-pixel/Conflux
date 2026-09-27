from django.urls import path

from . import views

urlpatterns = [
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/page/",
        views.PageDetailView.as_view(),
        name="page-detail",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/page/blocks/",
        views.PageBlockListView.as_view(),
        name="page-block-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/page/blocks/reorder/",
        views.PageBlockReorderView.as_view(),
        name="page-block-reorder",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/page/blocks/<uuid:block_public_id>/",
        views.PageBlockDetailView.as_view(),
        name="page-block-detail",
    ),
]
