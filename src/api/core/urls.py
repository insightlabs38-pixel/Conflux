from django.urls import include, path

from .views import health

urlpatterns = [
    path("health/", health, name="health"),
    path("accounts/", include("accounts.urls")),
    path("workspaces/", include("workspaces.urls")),
    path("audit/", include("audit.urls")),
    path("", include("events.urls")),
    path("", include("integrations.urls")),
    path("", include("stages.urls")),
    path("", include("policies.urls")),
    path("", include("participation.urls")),
]
