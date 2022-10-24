from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from homebrew import views

app_name = 'homebrew'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),

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

    path(
        'xhr_create/item/<int:character_pk>',
        staff_member_required(views.XhrCreateItemView.as_view()),
        name='xhr_create_item'),
    path(
        'create/item/<int:character_pk>',
        views.CreateItemView.as_view(),
        name='create_item'),

    path(
        'xhr_create/riot_gear/<int:character_pk>',
        views.XhrCreateRiotGearView.as_view(),
        name='xhr_create_riot_gear'),
    path(
        'create/riot_gear/<int:character_pk>',
        views.CreateRiotGearView.as_view(),
        name='create_riot_gear'),

    path(
        'xhr_create/weapon/<int:character_pk>',
        views.XhrCreateWeaponView.as_view(),
        name='xhr_create_weapon'),
    path(
        'create/weapon/<int:character_pk>',
        views.CreateWeaponView.as_view(),
        name='create_weapon'),

    path(
        'xhr_create/basespell/<int:character_pk>',
        views.XhrCreateBaseSpellView.as_view(),
        name='xhr_create_base_spell'),
    path(
        'create/basespell/<int:character_pk>',
        views.CreateBaseSpellView.as_view(),
        name='create_base_spell'),
]
