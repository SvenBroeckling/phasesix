from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from homebrew import views

app_name = 'homebrew'

urlpatterns = [
    url('^$', views.IndexView.as_view(), name='index'),

    path(
        'process/item/<int:item_pk>/<str:mode>',
        staff_member_required(views.ProcessItemView.as_view()),
        name='process_item'),
    path(
        'process/weapon/<int:weapon_pk>/<str:mode>',
        staff_member_required(views.ProcessWeaponView.as_view()),
        name='process_weapon'),
    path(
        'process/riot_gear/<int:riot_gear_pk>/<str:mode>',
        staff_member_required(views.ProcessRiotGearView.as_view()),
        name='process_riot_gear'),
    path(
        'process/base_spell/<int:base_spell_pk>/<str:mode>',
        staff_member_required(views.ProcessBaseSpellView.as_view()),
        name='process_base_spell'),

    url(
        r'^xhr_create/item/(?P<character_pk>\d+)$',
        staff_member_required(views.XhrCreateItemView.as_view()),
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

    url(
        r'^xhr_create/basespell/(?P<character_pk>\d+)$',
        views.XhrCreateBaseSpellView.as_view(),
        name='xhr_create_base_spell'),
    url(
        r'^create/basespell/(?P<character_pk>\d+)$',
        views.CreateBaseSpellView.as_view(),
        name='create_base_spell'),
]
