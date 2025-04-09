from django.urls import path, reverse_lazy
from django.views.generic import RedirectView

from magic import views

app_name = "magic"

urlpatterns = [
    path("spell/origins/", views.SpellOriginView.as_view(), name="spell_origin_list"),
    path(
        "spell/list/<int:origin_pk>",
        RedirectView.as_view(url=reverse_lazy("magic:spell_origin_list")),
        name="basespell_list",
    ),
    path(
        "spell/detail/<int:pk>",
        views.BaseSpellDetailView.as_view(),
        name="basespell_detail",
    ),
]
