from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from curators_desk import views

app_name = "curators_desk"

urlpatterns = [
    path("", staff_member_required(views.DashboardView.as_view()), name="dashboard"),
    path(
        "roll_statistics/",
        views.RollStatisticsView.as_view(),
        name="roll_statistics",
    ),
    path(
        "template_statistics/",
        views.TemplateStatisticsView.as_view(),
        name="template_statistics",
    ),
    path(
        "templates_by_id/",
        views.TemplatesByIdView.as_view(),
        name="templates_by_id",
    ),
    path(
        "extension_grid/<type>/",
        staff_member_required(views.ExtensionGrid.as_view()),
        name="extension_grid",
    ),
    path(
        "translation_status/",
        views.TranslationStatusView.as_view(),
        name="translation_status",
    ),
    path(
        "review_homebrew/",
        views.ReviewHomebrewView.as_view(),
        name="review_homebrew",
    ),
    path(
        "keep_homebrew/",
        staff_member_required(views.KeepHomebrewView.as_view()),
        name="keep_homebrew",
    ),
    path(
        "accept_homebrew/",
        staff_member_required(views.AcceptHomebrewView.as_view()),
        name="accept_homebrew",
    ),
    path(
        "update_homebrew/",
        staff_member_required(views.UpdateHomebrewView.as_view()),
        name="update_homebrew",
    ),
    path(
        "translate_homebrew/",
        staff_member_required(views.TranslateHomebrewView.as_view()),
        name="translate_homebrew",
    ),
    path(
        "generate_homebrew_image/",
        staff_member_required(views.GenerateHomebrewImageView.as_view()),
        name="generate_homebrew_image",
    ),
]
