from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

app_name = "partypad"

urlpatterns = [
    path("partypad/", login_required(views.IndexView.as_view()), name="index"),
    path(
        "partypad/<uuid:pad_id>/",
        login_required(views.DetailView.as_view()),
        name="detail",
    ),
    path(
        "partypad/<uuid:pad_id>/upload/",
        login_required(views.UploadView.as_view()),
        name="upload",
    ),
    path(
        "partypad/<uuid:pad_id>/objects/",
        login_required(views.UpsertObjectView.as_view()),
        name="upsert_object",
    ),
    path(
        "partypad/<uuid:pad_id>/objects/<uuid:object_id>/delete/",
        login_required(views.DeleteObjectView.as_view()),
        name="delete_object",
    ),
]
