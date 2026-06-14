from django.urls import path
from . import views

app_name = "essential_characters"

urlpatterns = [
    path("marks/summary/", views.MarkSummaryView.as_view(), name="mark_summary"),
    path(
        "equipment/summary/",
        views.EquipmentSummaryView.as_view(),
        name="equipment_summary",
    ),
    path(
        "supernatural/summary/",
        views.SupernaturalSummaryView.as_view(),
        name="supernatural_summary",
    ),
    path(
        "new/",
        views.EssentialCharacterCreateWizard.as_view(
            views.WIZARD_FORMS,
            condition_dict={
                "supernatural": views.EssentialCharacterCreateWizard.show_supernatural_step
            },
        ),
        name="create",
    ),
    path(
        "<slug:slug>/info/<str:section>/",
        views.EssentialCharacterDetailInfoView.as_view(),
        name="detail_info",
    ),
    path(
        "<slug:slug>/image/",
        views.EssentialCharacterImageView.as_view(),
        name="change_image",
    ),
    path(
        "<slug:slug>/edit/<str:section>/",
        views.EssentialCharacterEditSectionView.as_view(),
        name="edit_section",
    ),
    path(
        "<slug:slug>/condition/<str:condition>/",
        views.EssentialCharacterConditionView.as_view(),
        name="set_condition",
    ),
    path(
        "<slug:slug>/edit-search/",
        views.EssentialCharacterEditSearchView.as_view(),
        name="edit_search",
    ),
    path("<slug:slug>/", views.EssentialCharacterDetailView.as_view(), name="detail"),
    path(
        "<slug:slug>/edit/", views.EssentialCharacterUpdateView.as_view(), name="edit"
    ),
]
