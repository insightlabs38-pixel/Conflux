from accounts.credential_views import CredentialRevokeView, CredentialView
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

from .approval_views import (
    ApprovalCancelView,
    ApprovalDecisionView,
    ApprovalDetailView,
    ApprovalGateListView,
    ApprovalGateView,
    ApprovalListView,
)
from .entity_views import EntityCatalogueView, EntityQueryView
from .job_views import JobArtifactView, JobCancelView, JobDetailView, JobListView
from .rich_views import RichPreviewView
from .saved_view_views import SavedViewDetailView, SavedViewListView, SavedViewRunView
from .thread_views import ThreadCommentView, ThreadView
from .timeline_views import TimelineView
from .views import health

urlpatterns = [
    path("health/", health, name="health"),
    path("schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "workspaces/<uuid:workspace_public_id>/api-credentials/",
        CredentialView.as_view(),
        name="api-credential-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/api-credentials/<uuid:credential_public_id>/revoke/",
        CredentialRevokeView.as_view(),
        name="api-credential-revoke",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/rich/preview/",
        RichPreviewView.as_view(),
        name="rich-preview",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/entities/",
        EntityCatalogueView.as_view(),
        name="entity-catalogue",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/entities/<slug:entity_key>/",
        EntityQueryView.as_view(),
        name="entity-query",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/views/",
        SavedViewListView.as_view(),
        name="saved-view-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/views/<uuid:view_public_id>/",
        SavedViewDetailView.as_view(),
        name="saved-view-detail",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/views/<uuid:view_public_id>/run/",
        SavedViewRunView.as_view(),
        name="saved-view-run",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/timeline/",
        TimelineView.as_view(),
        name="event-timeline",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/threads/<slug:subject_type>/<str:subject_id>/<slug:audience>/",
        ThreadView.as_view(),
        name="thread",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/thread-comments/<uuid:comment_public_id>/",
        ThreadCommentView.as_view(),
        name="thread-comment",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/approvals/",
        ApprovalListView.as_view(),
        name="approval-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/approvals/<uuid:approval_public_id>/",
        ApprovalDetailView.as_view(),
        name="approval-detail",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/approvals/<uuid:approval_public_id>/decision/",
        ApprovalDecisionView.as_view(),
        name="approval-decision",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/approvals/<uuid:approval_public_id>/cancel/",
        ApprovalCancelView.as_view(),
        name="approval-cancel",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/approval-gates/",
        ApprovalGateListView.as_view(),
        name="approval-gate-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/approval-gates/<slug:action>/",
        ApprovalGateView.as_view(),
        name="approval-gate",
    ),
    path("workspaces/<uuid:workspace_public_id>/jobs/", JobListView.as_view(), name="job-list"),
    path(
        "workspaces/<uuid:workspace_public_id>/jobs/<uuid:job_public_id>/",
        JobDetailView.as_view(),
        name="job-detail",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/jobs/<uuid:job_public_id>/cancel/",
        JobCancelView.as_view(),
        name="job-cancel",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/jobs/<uuid:job_public_id>/artifacts/<str:artifact_name>/",
        JobArtifactView.as_view(),
        name="job-artifact",
    ),
    path("accounts/", include("accounts.urls")),
    path("workspaces/", include("workspaces.urls")),
    path("audit/", include("audit.urls")),
    path("", include("events.urls")),
    path("", include("eventconfig.urls")),
    path("", include("integrations.urls")),
    path("", include("stages.urls")),
    path("", include("policies.urls")),
    path("", include("participation.urls")),
    path("", include("projects.urls")),
    path("", include("forms.urls")),
    path("", include("artifacts.urls")),
    path("", include("presentation.urls")),
    path("", include("evaluations.urls")),
    path("", include("community.urls")),
    path("", include("awards.urls")),
    path("", include("communications.urls")),
    path("", include("taxonomy.urls")),
    path("", include("eligibility.urls")),
    path("", include("deliberation.urls")),
    path("", include("onsite.urls")),
    path("", include("mentorship.urls")),
    path("", include("governance.urls")),
    path("", include("mcp_adapter.urls")),
    path("", include("portfolio.urls")),
    path("", include("continuation.urls")),
]
