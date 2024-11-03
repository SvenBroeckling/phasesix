from django.urls import path

from armory import views

app_name = "armory"

urlpatterns = [
    path("marterial/", views.MaterialOverviewView.as_view(), name="material_overview"),
    path("weapons/", views.WeaponListView.as_view(), name="weapon_list"),
    path("riot_gear/", views.RiotGearListView.as_view(), name="riot_gear_list"),
    path("items/", views.ItemListView.as_view(), name="item_list"),
    path("items/<int:pk>/", views.ItemDetailView.as_view(), name="item_detail"),
]
