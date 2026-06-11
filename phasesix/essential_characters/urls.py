from django.urls import path
from . import views

app_name = "essential_characters"

urlpatterns = [
    path("new/", views.EssentialCharacterCreateView.as_view(), name="create"),
    path("<slug:slug>/", views.EssentialCharacterDetailView.as_view(), name="detail"),
    path("<slug:slug>/edit/", views.EssentialCharacterUpdateView.as_view(), name="edit"),
]
