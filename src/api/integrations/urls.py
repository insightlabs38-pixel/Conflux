from django.urls import path

from . import views

urlpatterns = [
    path("gallery/", views.GalleryView.as_view(), name="integrations-gallery"),
    path("submit/", views.SubmitView.as_view(), name="integrations-submit"),
    path("judge/scores/", views.JudgeScoresView.as_view(), name="integrations-judge-scores"),
    path("export.csv", views.CsvExportView.as_view(), name="integrations-csv-export"),
]
