from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from curators_desk import views

app_name = "curators_desk"

urlpatterns = [
    path("", staff_member_required(views.DashboardView.as_view()), name="dashboard"),
]
