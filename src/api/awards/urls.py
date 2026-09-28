from django.urls import path

from . import fulfillment_export, sponsor_portal, views

_prefix = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/awards/"

urlpatterns = [
    path(
        "events/<uuid:event_public_id>/awards/",
        views.PublicAwardsView.as_view(),
        name="public-awards",
    ),
    path(_prefix, views.AwardListView.as_view(), name="award-list"),
    path(
        _prefix + "fulfillment-export/",
        fulfillment_export.FulfillmentExportView.as_view(),
        name="award-fulfillment-export",
    ),
    path(
        _prefix + "fulfillment-export.csv",
        fulfillment_export.FulfillmentExportCsvView.as_view(),
        name="award-fulfillment-export-csv",
    ),
    path(_prefix + "candidates/", views.AwardCandidateView.as_view(), name="award-candidates"),
    path(_prefix + "proposals/", views.AwardProposalView.as_view(), name="award-proposals"),
    path(
        _prefix + "<uuid:award_public_id>/winners/",
        views.AwardWinnerView.as_view(),
        name="award-winner-create",
    ),
    path(
        _prefix + "<uuid:award_public_id>/publish/",
        views.AwardPublishView.as_view(),
        name="award-publish",
    ),
    path(
        _prefix + "<uuid:award_public_id>/components/",
        views.AwardComponentView.as_view(),
        name="award-component-create",
    ),
    path(
        _prefix + "<uuid:award_public_id>/fulfillments/<uuid:fulfillment_public_id>/",
        views.FulfillmentView.as_view(),
        name="award-fulfillment",
    ),
    path(
        _prefix + "<uuid:award_public_id>/sponsors/<uuid:user_public_id>/",
        views.AwardSponsorView.as_view(),
        name="award-sponsor",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/sponsor-portal/awards/",
        sponsor_portal.SponsorPortalAwardListView.as_view(),
        name="sponsor-portal-award-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>"
        "/sponsor-portal/fulfillments/<uuid:fulfillment_public_id>/",
        sponsor_portal.SponsorPortalFulfillmentView.as_view(),
        name="sponsor-portal-fulfillment",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>"
        "/sponsor-portal/awards/<uuid:award_public_id>/resources/",
        sponsor_portal.SponsorPortalResourceListView.as_view(),
        name="sponsor-portal-resource-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>"
        "/sponsor-portal/awards/<uuid:award_public_id>/resources/<uuid:resource_public_id>/",
        sponsor_portal.SponsorPortalResourceDetailView.as_view(),
        name="sponsor-portal-resource-detail",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/challenges/",
        views.ChallengeListView.as_view(),
        name="challenge-list",
    ),
]
