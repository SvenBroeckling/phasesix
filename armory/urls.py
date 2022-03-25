from django.conf.urls import url

from armory import views

app_name = 'armory'

urlpatterns = [
    url('^weapons/$', views.WeaponListView.as_view(), name='weapon_list'),
    url('^riot_gear/$', views.RiotGearListView.as_view(), name='riot_gear_list'),
]
