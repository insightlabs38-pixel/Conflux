from django.urls import path
from onsite import public_views as onsite_public

from . import site_views, stories

urlpatterns = [
    path("<uuid:event_public_id>/finalists/", site_views.finalists, name="site-finalists"),
    path("<uuid:event_public_id>/results/", stories.results, name="site-results"),
    path(
        "<uuid:event_public_id>/results/awards/<uuid:award_public_id>/",
        stories.award_story,
        name="site-award-story",
    ),
    path(
        "<uuid:event_public_id>/results/awards/<uuid:award_public_id>/card.svg",
        stories.award_card,
        name="site-award-card",
    ),
    path(
        "<uuid:event_public_id>/results/projects/<uuid:project_public_id>/",
        stories.project_story,
        name="site-project-story",
    ),
    path(
        "<uuid:event_public_id>/results/projects/<uuid:project_public_id>/card.svg",
        stories.project_card,
        name="site-project-card",
    ),
    path("<uuid:event_public_id>/agenda/", onsite_public.agenda_page, name="site-agenda"),
    path("<uuid:event_public_id>/agenda.ics", onsite_public.agenda_ics, name="site-agenda-ics"),
    path("<uuid:event_public_id>/map/", onsite_public.expo_map, name="site-expo-map"),
    path("<uuid:event_public_id>/badge.svg", onsite_public.badge, name="site-badge"),
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
