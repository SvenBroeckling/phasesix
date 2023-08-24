from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from gmtools import views

app_name = "gmtools"

urlpatterns = [
    path(
        "translation_status/",
        staff_member_required(views.TranslationStatusView.as_view()),
        name="translation_status",
    ),
    path(
        "template_statistics/",
        staff_member_required(views.TemplateStatisticsView.as_view()),
        name="template_statistics",
    ),
    path(
        "extension_grid/<type>/",
        staff_member_required(views.ExtensionGrid.as_view()),
        name="extension_grid",
    ),
]
