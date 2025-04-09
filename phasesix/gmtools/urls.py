from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from gmtools import views

app_name = "gmtools"

urlpatterns = [
    path(
        "translation_status/",
        views.TranslationStatusView.as_view(),
        name="translation_status",
    ),
    path(
        "template_statistics/",
        views.TemplateStatisticsView.as_view(),
        name="template_statistics",
    ),
    path(
        "roll_statistics/",
        views.RollStatisticsView.as_view(),
        name="roll_statistics",
    ),
    path(
        "extension_grid/<type>/",
        staff_member_required(views.ExtensionGrid.as_view()),
        name="extension_grid",
    ),
]
