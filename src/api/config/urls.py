from django.urls import include, path

urlpatterns = [
    path("api/v1/", include("core.urls")),
    # Public, unauthenticated, server-rendered site (GAL-001/GAL-002): real
    # content in the raw HTML response, no JS execution required.
    path("e/", include("presentation.site_urls")),
    # Django's built-in language switcher (VS23): POSTing here with a
    # `language` field sets the `django_language` cookie LocaleMiddleware
    # reads on subsequent requests.
    path("e/i18n/", include("django.conf.urls.i18n")),
]
