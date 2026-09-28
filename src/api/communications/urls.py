from django.urls import path

from . import views
from .analytics_views import EventAnalyticsView
from .bulk_views import BulkOperationsView
from .moderation_views import ModerationQueueView, ModerationReviewsView
from .public_qa import (
    AnnouncementReviewView,
    CommunicationReviewView,
    PublicAnnouncementsView,
    PublicQuestionsView,
    QuestionsView,
)

_prefix = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/"

urlpatterns = [
    path(
        "events/<uuid:event_public_id>/questions/",
        PublicQuestionsView.as_view(),
        name="public-questions",
    ),
    path(
        "events/<uuid:event_public_id>/announcements/",
        PublicAnnouncementsView.as_view(),
        name="public-announcements",
    ),
    path(_prefix + "communications/questions/", QuestionsView.as_view(), name="event-questions"),
    path(
        _prefix + "communications/questions/<uuid:source_public_id>/review/",
        CommunicationReviewView.as_view(),
        name="question-review",
    ),
    path(
        _prefix + "communications/announcements/<uuid:source_public_id>/review/",
        AnnouncementReviewView.as_view(),
        name="announcement-review",
    ),
    path(_prefix + "operations/analytics/", EventAnalyticsView.as_view(), name="event-analytics"),
    path(
        _prefix + "operations/moderation/", ModerationQueueView.as_view(), name="moderation-queue"
    ),
    path(
        _prefix + "operations/moderation/reviews/",
        ModerationReviewsView.as_view(),
        name="moderation-reviews",
    ),
    path(_prefix + "operations/bulk/", BulkOperationsView.as_view(), name="operations-bulk"),
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
