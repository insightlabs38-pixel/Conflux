from django.urls import path

from . import record_views, views
from .public_api import PublicGalleryView

urlpatterns = [
    path(
        "events/<uuid:event_public_id>/gallery/",
        PublicGalleryView.as_view(),
        name="public-gallery",
    ),
    path(
        "records/verification-key/",
        record_views.VerificationKeyView.as_view(),
        name="record-verification-key",
    ),
    path("records/verify/", record_views.VerifyRecordView.as_view(), name="record-verify"),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/records/event/",
        record_views.EventRecordView.as_view(),
        name="event-record",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/records/project/",
        record_views.ProjectRecordView.as_view(),
        name="project-record",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/records/judge/",
        record_views.JudgeRecordView.as_view(),
        name="judge-record",
    ),
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
