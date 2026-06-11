from django.urls import path
from . import views

app_name = "essential_characters"

urlpatterns = [
    path("marks/summary/", views.mark_summary, name="mark_summary"),
    path("equipment/summary/", views.equipment_summary, name="equipment_summary"),
    path(
        "new/",
        views.EssentialCharacterCreateWizard.as_view(
            views.WIZARD_FORMS,
            condition_dict={"supernatural": views.show_supernatural_step},
        ),
        name="create",
    ),
    path("<slug:slug>/", views.EssentialCharacterDetailView.as_view(), name="detail"),
    path("<slug:slug>/edit/", views.EssentialCharacterUpdateView.as_view(), name="edit"),
]
