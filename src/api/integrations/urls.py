from django.urls import path

from . import (
    archive_views,
    external_qualifier_views,
    privacy_views,
    template_views,
    views,
    webhook_views,
)

_event = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/"

urlpatterns = [
    path(
        _event + "privacy/retention-policy/",
        privacy_views.RetentionPolicyView.as_view(),
        name="event-retention-policy",
    ),
    path(
        _event + "privacy/retention/run/",
        privacy_views.RetentionRunView.as_view(),
        name="event-retention-run",
    ),
    path(
        _event + "privacy/subjects/<uuid:user_public_id>/export/",
        privacy_views.SubjectExportView.as_view(),
        name="event-privacy-export",
    ),
    path(
        _event + "privacy/subjects/<uuid:user_public_id>/erase/",
        privacy_views.SubjectErasureView.as_view(),
        name="event-privacy-erase",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/archive/",
        archive_views.EventArchiveExportView.as_view(),
        name="event-archive-export",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/archive/signed/",
        archive_views.EventSignedArchiveExportView.as_view(),
        name="event-signed-archive-export",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/archive/import/",
        archive_views.WorkspaceArchiveImportView.as_view(),
        name="workspace-archive-import",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/archive/signed/import/",
        archive_views.WorkspaceSignedArchiveImportView.as_view(),
        name="workspace-signed-archive-import",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/archive/preview/",
        archive_views.WorkspaceArchivePreviewView.as_view(),
        name="workspace-archive-preview",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/event-templates/",
        template_views.EventTemplateListView.as_view(),
        name="event-template-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/event-templates/library/",
        template_views.TemplateLibraryListView.as_view(),
        name="event-template-library",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/event-templates/library/<slug:template_slug>/instantiate/",
        template_views.TemplateLibraryInstantiateView.as_view(),
        name="event-template-library-instantiate",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/event-templates/<uuid:template_public_id>/",
        template_views.EventTemplateDetailView.as_view(),
        name="event-template-detail",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/event-templates/<uuid:template_public_id>/instantiate/",
        template_views.EventTemplateInstantiateView.as_view(),
        name="event-template-instantiate",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/clone/",
        template_views.EventCloneView.as_view(),
        name="event-clone",
    ),
    path(
        (
            "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/stages/"
            "<uuid:stage_public_id>/external-qualifiers/"
        ),
        external_qualifier_views.ExternalQualifierImportView.as_view(),
        name="external-qualifier-import",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/webhooks/",
        webhook_views.WebhookSubscriptionsView.as_view(),
        name="webhook-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/webhooks/<uuid:subscription_public_id>/",
        webhook_views.WebhookSubscriptionView.as_view(),
        name="webhook-detail",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/webhooks/<uuid:subscription_public_id>/deliveries/",
        webhook_views.WebhookDeliveriesView.as_view(),
        name="webhook-deliveries",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/webhooks/<uuid:subscription_public_id>/deliveries/<uuid:delivery_public_id>/replay/",
        webhook_views.WebhookReplayView.as_view(),
        name="webhook-replay",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/webhooks/<uuid:subscription_public_id>/deliveries/<uuid:delivery_public_id>/",
        webhook_views.WebhookInspectionView.as_view(),
        name="webhook-inspection",
    ),
    path("gallery/", views.GalleryView.as_view(), name="integrations-gallery"),
    path("submit/", views.SubmitView.as_view(), name="integrations-submit"),
    path("judge/scores/", views.JudgeScoresView.as_view(), name="integrations-judge-scores"),
    path("export.csv", views.CsvExportView.as_view(), name="integrations-csv-export"),
]
