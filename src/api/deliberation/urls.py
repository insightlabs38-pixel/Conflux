from django.urls import path

from . import views

_room = (
    "workspaces/<uuid:workspace_public_id>/events/<uuid:event_public_id>"
    "/awards/<uuid:award_public_id>/deliberation/"
)

urlpatterns = [
    path(_room, views.RoomView.as_view(), name="deliberation-room"),
    path(_room + "notes/", views.NoteView.as_view(), name="deliberation-notes"),
    path(
        _room + "projects/<uuid:project_public_id>/stance/",
        views.StanceView.as_view(),
        name="deliberation-stance",
    ),
    path(_room + "close/", views.CloseView.as_view(), name="deliberation-close"),
    path(_room + "finalize/", views.FinalizeView.as_view(), name="deliberation-finalize"),
]
