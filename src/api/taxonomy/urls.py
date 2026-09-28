from django.urls import path

from . import views

urlpatterns = [
    path(
        "workspaces/<uuid:workspace_public_id>/taxonomies/",
        views.TaxonomyListView.as_view(),
        name="taxonomy-list",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/taxonomies/<uuid:taxonomy_public_id>/",
        views.TaxonomyDetailView.as_view(),
        name="taxonomy-detail",
    ),
    path(
        "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>/taxonomy-assignments/",
        views.AssignmentView.as_view(),
        name="taxonomy-assignments",
    ),
]
