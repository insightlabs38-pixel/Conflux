from django.urls import path

from . import record_views, views
from .conformance_views import ConformanceReportView
from .public_api import PublicGalleryView
from .publication_views import PublicationDetailView, PublicationListView, PublicFinalistsView
from .search import ProjectTagsView, PublicSearchView, SavedSearchDetailView, SavedSearchListView

_prefix = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/"

urlpatterns = [
    path(
        _prefix + "publication-schedules/",
        PublicationListView.as_view(),
        name="publication-schedule-list",
    ),
    path(
        _prefix + "publication-schedules/<str:surface>/",
        PublicationDetailView.as_view(),
        name="publication-schedule-detail",
    ),
    path(
        "events/<uuid:event_public_id>/finalists/",
        PublicFinalistsView.as_view(),
        name="public-finalists",
    ),
    path(
        _prefix + "accessibility-conformance/",
        ConformanceReportView.as_view(),
        name="accessibility-conformance",
    ),
    path("events/<uuid:event_public_id>/search/", PublicSearchView.as_view(), name="public-search"),
    path(
        _prefix + "projects/<uuid:project_public_id>/tags/",
        ProjectTagsView.as_view(),
        name="project-tags",
    ),
    path(_prefix + "saved-searches/", SavedSearchListView.as_view(), name="saved-search-list"),
    path(
        _prefix + "saved-searches/<uuid:view_public_id>/",
        SavedSearchDetailView.as_view(),
        name="saved-search-detail",
    ),
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
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/page/accessibility-audit/",
        views.PageAccessibilityAuditView.as_view(),
        name="page-accessibility-audit",
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
