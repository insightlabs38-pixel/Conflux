from django.urls import path

from . import views

_prefix = "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/"

urlpatterns = [
    path(_prefix + "policy-debug/", views.PolicyDebugView.as_view(), name="policy-debug"),
    path(_prefix + "policy-presets/", views.PresetListView.as_view(), name="policy-preset-list"),
    path(_prefix + "policies/", views.PolicyListView.as_view(), name="policy-list"),
    path(
        _prefix + "policies/<uuid:policy_public_id>/",
        views.PolicyDetailView.as_view(),
        name="policy-detail",
    ),
    path(
        _prefix + "policy-bindings/",
        views.PolicyBindingListView.as_view(),
        name="policy-binding-list",
    ),
    path(
        _prefix + "policy-bindings/<uuid:binding_public_id>/",
        views.PolicyBindingDetailView.as_view(),
        name="policy-binding-detail",
    ),
    path(
        _prefix + "temporal-gates/", views.TemporalGateListView.as_view(), name="temporal-gate-list"
    ),
    path(
        _prefix + "temporal-gates/<uuid:gate_public_id>/",
        views.TemporalGateDetailView.as_view(),
        name="temporal-gate-detail",
    ),
    path(
        _prefix + "exception-grants/",
        views.ExceptionGrantListView.as_view(),
        name="exception-grant-list",
    ),
    path(
        _prefix + "timezone-timeline/",
        views.TimezoneTimelineView.as_view(),
        name="timezone-timeline",
    ),
]
