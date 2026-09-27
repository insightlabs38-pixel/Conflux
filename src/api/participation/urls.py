from django.urls import path

from . import marketplace_views, views

_prefix = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/"

urlpatterns = [
    path(
        _prefix + "marketplace/profile/",
        marketplace_views.MyMarketplaceProfileView.as_view(),
        name="marketplace-profile",
    ),
    path(
        _prefix + "marketplace/profiles/",
        marketplace_views.MarketplaceProfilesView.as_view(),
        name="marketplace-profiles",
    ),
    path(
        _prefix + "marketplace/openings/",
        marketplace_views.TeamOpeningListView.as_view(),
        name="marketplace-openings",
    ),
    path(
        _prefix + "marketplace/my-openings/",
        marketplace_views.MyTeamOpeningsView.as_view(),
        name="marketplace-my-openings",
    ),
    path(
        _prefix + "marketplace/openings/<uuid:opening_public_id>/",
        marketplace_views.TeamOpeningDetailView.as_view(),
        name="marketplace-opening-detail",
    ),
    path(
        _prefix + "marketplace/openings/<uuid:opening_public_id>/matches/",
        marketplace_views.OpeningMatchesView.as_view(),
        name="marketplace-opening-matches",
    ),
    path(
        _prefix + "marketplace/matches/",
        marketplace_views.MarketplaceMatchesView.as_view(),
        name="marketplace-matches",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/participant-events/",
        views.ParticipantEventListView.as_view(),
        name="participant-events",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/judge-events/",
        views.JudgeEventListView.as_view(),
        name="judge-events",
    ),
    path(_prefix + "my-team/", views.MyTeamView.as_view(), name="my-team"),
    path(_prefix + "my-team/leave/", views.LeaveTeamView.as_view(), name="my-team-leave"),
    path(
        _prefix + "my-team/transfer-captain/",
        views.TransferCaptainView.as_view(),
        name="my-team-transfer-captain",
    ),
    path(
        _prefix + "my-team/invites/",
        views.TeamInviteListView.as_view(),
        name="my-team-invite-list",
    ),
    path(
        _prefix + "my-team/invites/<uuid:invite_public_id>/",
        views.TeamInviteDetailView.as_view(),
        name="my-team-invite-detail",
    ),
    path(
        _prefix + "team-invites/redeem/",
        views.RedeemInviteView.as_view(),
        name="team-invite-redeem",
    ),
]
