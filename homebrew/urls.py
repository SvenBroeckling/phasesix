from django.conf.urls import url

from homebrew import views

app_name = 'homebrew'

urlpatterns = [
    url('^$', views.IndexView.as_view(), name='index'),
    url(
        r'^xhr_create/item/(?P<character_pk>\d+)$',
        views.XhrCreateItemView.as_view(),
        name='xhr_create_item'),
    url(
        r'^create/item/(?P<character_pk>\d+)$',
        views.CreateItemView.as_view(),
        name='create_item'),

    url(
        r'^xhr_create/riot_gear/(?P<character_pk>\d+)$',
        views.XhrCreateRiotGearView.as_view(),
        name='xhr_create_riot_gear'),
    url(
        r'^create/riot_gear/(?P<character_pk>\d+)$',
        views.CreateRiotGearView.as_view(),
        name='create_riot_gear'),

    url(
        r'^xhr_create/weapon/(?P<character_pk>\d+)$',
        views.XhrCreateWeaponView.as_view(),
        name='xhr_create_weapon'),
    url(
        r'^create/weapon/(?P<character_pk>\d+)$',
        views.CreateWeaponView.as_view(),
        name='create_weapon'),
]
