from django.urls import path

from . import views

_prefix = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/"

urlpatterns = [
    path(_prefix + "mentors/", views.MentorProfileListView.as_view(), name="mentor-profile-list"),
    path(
        _prefix + "mentors/me/", views.MentorProfileSelfView.as_view(), name="mentor-profile-self"
    ),
    path(
        _prefix + "projects/<uuid:project_public_id>/mentor-requests/",
        views.ProjectMentorRequestView.as_view(),
        name="project-mentor-request-list",
    ),
    path(
        _prefix + "mentor-requests/queue/",
        views.MentorRequestQueueView.as_view(),
        name="mentor-request-queue",
    ),
    path(
        _prefix + "mentor-requests/<uuid:request_public_id>/claim/",
        views.MentorRequestClaimView.as_view(),
        name="mentor-request-claim",
    ),
    path(
        _prefix + "mentor-requests/<uuid:request_public_id>/reassign/",
        views.MentorRequestReassignView.as_view(),
        name="mentor-request-reassign",
    ),
    path(
        _prefix + "mentor-requests/<uuid:request_public_id>/resolve/",
        views.MentorRequestResolveView.as_view(),
        name="mentor-request-resolve",
    ),
    path(
        _prefix + "mentor-requests/<uuid:request_public_id>/cancel/",
        views.MentorRequestCancelView.as_view(),
        name="mentor-request-cancel",
    ),
    path(
        _prefix + "office-hours/",
        views.OfficeHourSlotListView.as_view(),
        name="office-hour-slot-list",
    ),
    path(
        _prefix + "office-hours/<uuid:slot_public_id>/signups/",
        views.OfficeHourSignupListView.as_view(),
        name="office-hour-signup-list",
    ),
    path(
        _prefix + "office-hours/signups/<uuid:signup_public_id>/",
        views.OfficeHourSignupDetailView.as_view(),
        name="office-hour-signup-detail",
    ),
]
