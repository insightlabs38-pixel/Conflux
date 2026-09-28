from django.urls import path

from . import views

_w = "workspaces/<uuid:workspace_public_id>/portfolio/"

urlpatterns = [
    path(_w + "me/", views.MyPortfolioView.as_view(), name="portfolio-me"),
    path(_w + "projects/", views.PortfolioProjectListView.as_view(), name="portfolio-projects"),
    path(
        _w + "participants/",
        views.PortfolioParticipantListView.as_view(),
        name="portfolio-participants",
    ),
    path(
        _w + "participants/<uuid:user_public_id>/",
        views.PortfolioParticipantDetailView.as_view(),
        name="portfolio-participant",
    ),
]
