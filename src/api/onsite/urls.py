from django.urls import path

from . import route_views, views

_e = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/"

urlpatterns = [
    path(_e + "locations/", views.LocationListView.as_view(), name="onsite-locations"),
    path(_e + "locations/auto-assign/", views.AutoAssignView.as_view(), name="onsite-auto-assign"),
    path(
        _e + "locations/<uuid:location_public_id>/",
        views.LocationDetailView.as_view(),
        name="onsite-location-detail",
    ),
    path(
        _e + "project-locations/",
        views.ProjectLocationListView.as_view(),
        name="onsite-project-locations",
    ),
    path(
        _e + "projects/<uuid:project_public_id>/location/",
        views.ProjectLocationView.as_view(),
        name="onsite-project-location",
    ),
    path(_e + "my-attendance/", views.MyAttendanceView.as_view(), name="onsite-my-attendance"),
    path(_e + "attendance/", views.AttendanceListView.as_view(), name="onsite-attendance"),
    path(_e + "my-pass/", views.MyPassView.as_view(), name="onsite-my-pass"),
    path(_e + "my-pass/qr/", views.MyPassQrView.as_view(), name="onsite-my-pass-qr"),
    path(_e + "checkins/scan/", views.ScanView.as_view(), name="onsite-scan"),
    path(_e + "onsite-summary/", views.SummaryView.as_view(), name="onsite-summary"),
    path(
        _e + "stages/<uuid:stage_public_id>/evaluation-plans/<uuid:plan_public_id>/routes/",
        route_views.RoutesView.as_view(),
        name="onsite-routes",
    ),
    path(
        _e + "stages/<uuid:stage_public_id>/evaluation-plans/<uuid:plan_public_id>/my-route/",
        route_views.MyRouteView.as_view(),
        name="onsite-my-route",
    ),
]
