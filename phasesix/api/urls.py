from django.urls import path

app_name = "api"

from . import views

urlpatterns = [path("dump/<str:model>", views.DumpApiView.as_view(), name="dump_api")]
