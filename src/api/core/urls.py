from accounts.credential_views import CredentialRevokeView, CredentialView
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

from .views import health

urlpatterns = [
    path("health/", health, name="health"),
    path("schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "workspaces/<uuid:workspace_public_id>/api-credentials/",
        CredentialView.as_view(),
        name="api-credential-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/api-credentials/<uuid:credential_public_id>/revoke/",
        CredentialRevokeView.as_view(),
        name="api-credential-revoke",
    ),
    path("accounts/", include("accounts.urls")),
    path("workspaces/", include("workspaces.urls")),
    path("audit/", include("audit.urls")),
    path("", include("events.urls")),
    path("", include("integrations.urls")),
    path("", include("stages.urls")),
    path("", include("policies.urls")),
    path("", include("participation.urls")),
    path("", include("projects.urls")),
    path("", include("forms.urls")),
    path("", include("artifacts.urls")),
    path("", include("presentation.urls")),
    path("", include("evaluations.urls")),
    path("", include("community.urls")),
    path("", include("awards.urls")),
    path("", include("communications.urls")),
    path("", include("taxonomy.urls")),
    path("", include("eligibility.urls")),
    path("", include("deliberation.urls")),
    path("", include("onsite.urls")),
    path("", include("mentorship.urls")),
    path("", include("governance.urls")),
]
