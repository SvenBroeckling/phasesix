from django.urls import path

from rules import views

app_name = "rules"

urlpatterns = [
    path("templates/", views.TemplateListView.as_view(), name="template_list"),
    path("foes/", views.FoeListView.as_view(), name="foe_list"),
]
