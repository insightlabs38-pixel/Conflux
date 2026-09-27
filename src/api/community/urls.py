from django.urls import path

from . import views

_EVENT = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>"
_PROJECT = f"{_EVENT}/projects/<uuid:project_public_id>"
_PUBLIC_EVENT = "public/events/<uuid:event_public_id>"

urlpatterns = [
    path(f"{_EVENT}/voting-plan/", views.VotingPlanDetailView.as_view(), name="voting-plan-detail"),
    path(
        f"{_EVENT}/voting-plan/tokens/",
        views.VoteTokenBatchView.as_view(),
        name="voting-plan-tokens",
    ),
    path(
        f"{_EVENT}/voting-plan/publish-results/",
        views.ResultsPublishView.as_view(),
        name="voting-plan-publish-results",
    ),
    path(
        f"{_EVENT}/voting-plan/abuse-signals/",
        views.AbuseSignalListView.as_view(),
        name="voting-abuse-signals",
    ),
    path(
        f"{_EVENT}/voting-plan/abuse-signals/<uuid:signal_public_id>/resolve/",
        views.AbuseSignalResolveView.as_view(),
        name="voting-abuse-signal-resolve",
    ),
    path(f"{_EVENT}/voting-plan/audit/", views.CommunityAuditView.as_view(), name="voting-audit"),
    path(
        f"{_EVENT}/voting/candidates/",
        views.CandidateOrderView.as_view(),
        name="voting-candidates",
    ),
    path(f"{_EVENT}/voting/votes/", views.VoteCreateView.as_view(), name="voting-votes"),
    path(
        f"{_EVENT}/voting/request-email-token/",
        views.RequestEmailVoteTokenView.as_view(),
        name="voting-request-email-token",
    ),
    path(f"{_EVENT}/voting/results/", views.ResultsView.as_view(), name="voting-results"),
    path(
        f"{_EVENT}/voting/status/",
        views.PublicVotingStatusView.as_view(),
        name="voting-status",
    ),
    path(f"{_PROJECT}/comments/", views.CommentListCreateView.as_view(), name="comment-list"),
    path(
        f"{_PROJECT}/comments/<uuid:comment_public_id>/hide/",
        views.CommentHideView.as_view(),
        name="comment-hide",
    ),
    # Workspace-free equivalents for a genuinely anonymous voter following a
    # shared link, who has no reason to know the event's workspace id.
    path(
        f"{_PUBLIC_EVENT}/voting/candidates/",
        views.CandidateOrderView.as_view(),
        name="public-voting-candidates",
    ),
    path(
        f"{_PUBLIC_EVENT}/voting/votes/", views.VoteCreateView.as_view(), name="public-voting-votes"
    ),
    path(
        f"{_PUBLIC_EVENT}/voting/request-email-token/",
        views.RequestEmailVoteTokenView.as_view(),
        name="public-voting-request-email-token",
    ),
    path(
        f"{_PUBLIC_EVENT}/voting/results/",
        views.ResultsView.as_view(),
        name="public-voting-results",
    ),
    path(
        f"{_PUBLIC_EVENT}/voting/status/",
        views.PublicVotingStatusView.as_view(),
        name="public-voting-status",
    ),
]
