from django.urls import path

from . import views

_prefix = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/awards/"

urlpatterns = [
    path(
        "events/<uuid:event_public_id>/awards/",
        views.PublicAwardsView.as_view(),
        name="public-awards",
    ),
    path(_prefix, views.AwardListView.as_view(), name="award-list"),
    path(_prefix + "candidates/", views.AwardCandidateView.as_view(), name="award-candidates"),
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
]
