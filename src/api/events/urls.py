from django.urls import path

from . import views

urlpatterns = [
    path("events/<uuid:event_public_id>/", views.PublicEventView.as_view(), name="event-public"),
    path(
        "workspaces/<uuid:workspace_public_id>/events/",
        views.EventListView.as_view(),
        name="event-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/",
        views.EventDetailView.as_view(),
        name="event-detail",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/status/",
        views.EventStatusView.as_view(),
        name="event-status",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/dashboard/",
        views.EventDashboardView.as_view(),
        name="event-dashboard",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/tracks/",
        views.TrackListView.as_view(),
        name="track-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/tracks/<uuid:track_public_id>/",
        views.TrackDetailView.as_view(),
        name="track-detail",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/base-prizes/",
        views.BasePrizeListView.as_view(),
        name="base-prize-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/base-prizes/<uuid:prize_public_id>/",
        views.BasePrizeDetailView.as_view(),
        name="base-prize-detail",
    ),
]
