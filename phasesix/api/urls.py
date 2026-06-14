from django.urls import path

app_name = "api"

from essential_characters.api import PublicEssentialCharacterApiView

from . import views

urlpatterns = [
    path(
        "characters/essential/<slug:character_hash>",
        PublicEssentialCharacterApiView.as_view(),
        name="essential_character",
    ),
    path("dump/<str:model>", views.DumpApiView.as_view(), name="dump_api"),
    path(
        "upload_rulebook", views.UploadRulebooksView.as_view(), name="upload_rulebook"
    ),
]
