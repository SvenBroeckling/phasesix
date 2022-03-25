from django.conf.urls import url

from armory import views

app_name = 'armory'

urlpatterns = [
    url('^weapons/$', views.WeaponListView.as_view(), name='weapon_list'),
]
