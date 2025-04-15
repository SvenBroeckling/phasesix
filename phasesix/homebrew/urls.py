from django.urls import path

from homebrew import views

app_name = "homebrew"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
]
