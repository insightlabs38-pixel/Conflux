from django.urls import path

from . import views

_prefix = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/"

urlpatterns = [
    path(
        "workspaces/<uuid:workspace_public_id>/operator-console/",
        views.OperatorConsoleView.as_view(),
        name="operator-console",
    ),
    path(
        _prefix + "operations/summary/",
        views.OperationsSummaryView.as_view(),
        name="operations-summary",
    ),
    path(
        _prefix + "operations/checklist/",
        views.LaunchChecklistView.as_view(),
        name="launch-checklist",
    ),
    path(
        _prefix + "communications/audiences/",
        views.AudienceListView.as_view(),
        name="audience-list",
    ),
    path(
        _prefix + "communications/audiences/preview/",
        views.AudiencePreviewView.as_view(),
        name="audience-preview",
    ),
    path(
        _prefix + "communications/messages/",
        views.MessageListCreateView.as_view(),
        name="message-list-create",
    ),
    path(
        _prefix + "communications/reminders/",
        views.ReminderListCreateView.as_view(),
        name="reminder-list-create",
    ),
    path(
        _prefix + "communications/reminders/<uuid:reminder_public_id>/cancel/",
        views.ReminderCancelView.as_view(),
        name="reminder-cancel",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/inbox/",
        views.InboxListView.as_view(),
        name="inbox-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/inbox/<uuid:recipient_public_id>/read/",
        views.InboxReadView.as_view(),
        name="inbox-read",
    ),
]
