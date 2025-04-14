from django.urls import path

from body_modifications.views import BodyModificationTypeListView

app_name = "body_modifications"

urlpatterns = [
    path(
        "types/",
        BodyModificationTypeListView.as_view(),
        name="body_modification_type_list",
    ),
]
