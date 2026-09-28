from django.urls import path

from . import views

_e = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/"
_p = _e + "stages/<uuid:stage_public_id>/evaluation-plans/<uuid:plan_public_id>/"

urlpatterns = [
    path(
        _e + "governance/settings/",
        views.GovernanceSettingsView.as_view(),
        name="governance-settings",
    ),
    path(_e + "rules/", views.RulesView.as_view(), name="rules"),
    path(_e + "rules/acknowledge/", views.RulesAcknowledgeView.as_view(), name="rules-acknowledge"),
    path(
        _e + "rules/acknowledgements/",
        views.RulesAcknowledgementListView.as_view(),
        name="rules-acknowledgements",
    ),
    path(_e + "rules/<int:number>/", views.RulesVersionView.as_view(), name="rules-version"),
    path(
        _e + "result-publication-requests/",
        views.PublicationRequestListView.as_view(),
        name="result-publication-requests",
    ),
    *[
        path(
            _e + f"result-publication-requests/<uuid:request_public_id>/{action}/",
            views.PublicationRequestActionView.as_view(action=action),
            name=f"result-publication-request-{action}",
        )
        for action in ("approve", "reject", "cancel")
    ],
    path(
        _e + "result-corrections/",
        views.ResultCorrectionListView.as_view(),
        name="result-corrections",
    ),
    path(
        "events/<uuid:event_public_id>/result-corrections/",
        views.PublicResultCorrectionListView.as_view(),
        name="public-result-corrections",
    ),
    path(
        _e + "projects/<uuid:project_public_id>/submissions/<uuid:stage_public_id>/receipt/",
        views.SubmissionReceiptView.as_view(),
        name="submission-receipt",
    ),
    path(_p + "my-assignments/", views.MyAssignmentsView.as_view(), name="my-assignments"),
    path(
        _p + "my-assignments/<uuid:project_public_id>/respond/",
        views.AssignmentRespondView.as_view(),
        name="assignment-respond",
    ),
    path(
        _p + "assignment-responses/",
        views.AssignmentResponseSummaryView.as_view(),
        name="assignment-response-summary",
    ),
    path(
        _e + "projects/<uuid:project_public_id>/exception-requests/",
        views.ProjectExceptionRequestView.as_view(),
        name="project-exception-requests",
    ),
    path(
        _e + "exception-requests/",
        views.ExceptionRequestListView.as_view(),
        name="exception-requests",
    ),
    *[
        path(
            _e + f"exception-requests/<uuid:request_public_id>/{action}/",
            views.ExceptionRequestActionView.as_view(action=action),
            name=f"exception-request-{action}",
        )
        for action in ("approve", "reject", "cancel")
    ],
]
