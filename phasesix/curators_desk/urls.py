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
]
