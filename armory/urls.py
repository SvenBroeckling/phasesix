from django.urls import path

from armory import views

app_name = 'armory'

urlpatterns = [
    path('weapons/', views.WeaponListView.as_view(), name='weapon_list'),
    path('riot_gear/', views.RiotGearListView.as_view(), name='riot_gear_list'),
]
