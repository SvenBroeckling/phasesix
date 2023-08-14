from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from homebrew import views

app_name = 'homebrew'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),

    path(
        'xhr_create/item',
        staff_member_required(views.XhrCreateItemView.as_view()),
        name='xhr_create_item'),
    path(
        'create/item',
        views.CreateItemView.as_view(),
        name='create_item'),

    path(
        'xhr_create/riot_gear',
        views.XhrCreateRiotGearView.as_view(),
        name='xhr_create_riot_gear'),
    path(
        'create/riot_gear',
        views.CreateRiotGearView.as_view(),
        name='create_riot_gear'),

    path(
        'xhr_create/weapon',
        views.XhrCreateWeaponView.as_view(),
        name='xhr_create_weapon'),
    path(
        'create/weapon',
        views.CreateWeaponView.as_view(),
        name='create_weapon'),

    path(
        'xhr_create/basespell',
        views.XhrCreateBaseSpellView.as_view(),
        name='xhr_create_base_spell'),
    path(
        'create/basespell',
        views.CreateBaseSpellView.as_view(),
        name='create_base_spell'),
]
