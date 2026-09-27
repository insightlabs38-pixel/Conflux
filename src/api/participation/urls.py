from django.urls import path

from . import views

_prefix = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/"

urlpatterns = [
    path(
        "workspaces/<uuid:workspace_public_id>/participant-events/",
        views.ParticipantEventListView.as_view(),
        name="participant-events",
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
