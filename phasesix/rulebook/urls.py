from django.urls import path

from rulebook import views

app_name = "rulebook"

urlpatterns = [
    path("chapter/<int:pk>", views.ChapterDetailView.as_view(), name="detail"),
    path("download", views.DownloadView.as_view(), name="download"),
]
