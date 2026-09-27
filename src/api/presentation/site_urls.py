from django.urls import path

from . import site_views

urlpatterns = [
    path("sw.js", site_views.service_worker, name="site-service-worker"),
    path("verify/", site_views.verify, name="site-verify"),
    path("<uuid:event_public_id>/", site_views.event_landing, name="site-event"),
    path("<uuid:event_public_id>/gallery/", site_views.gallery, name="site-gallery"),
    path(
        "<uuid:event_public_id>/projects/<uuid:project_public_id>/",
        site_views.project_detail,
        name="site-project",
    ),
]
