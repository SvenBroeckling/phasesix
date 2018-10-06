from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from characters import views

app_name = 'characters'

urlpatterns = [
    url('^$', views.IndexView.as_view(), name='index'),
    url('^list/$', views.CharacterListView.as_view(), name='list'),
    url('^new/$', login_required(views.RandomCharacterView.as_view()), name='random_character'),
    url('^detail/(?P<pk>\d+)$', views.CharacterDetailView.as_view(), name='detail'),


    # gear
    url(
        '^xhr_buy_weapons/(?P<pk>\d+)$',
        views.XhrBuyWeaponsView.as_view(),
        name='xhr_buy_weapons'),

    url(
        '^buy_weapon/(?P<pk>\d+)/(?P<weapon_pk>\d+)$',
        views.BuyWeaponView.as_view(),
        name='buy_weapon'),
    url(
        '^sell_weapon/(?P<pk>\d+)/(?P<weapon_pk>\d+)$',
        views.SellWeaponView.as_view(),
        name='sell_weapon'),

    url(
        '^xhr_buy_riot_gear/(?P<pk>\d+)$',
        views.XhrBuyRiotGearView.as_view(),
        name='xhr_buy_riot_gear'),
    url(
        '^buy_riot_gear/(?P<pk>\d+)/(?P<riot_gear_pk>\d+)$',
        views.BuyRiotGearView.as_view(),
        name='buy_riot_gear'),
    url(
        '^sell_riot_gear/(?P<pk>\d+)/(?P<riot_gear_pk>\d+)$',
        views.SellRiotGearView.as_view(),
        name='sell_riot_gear'),

    url(
        '^xhr_buy_items/(?P<pk>\d+)$',
        views.XhrBuyItemsView.as_view(),
        name='xhr_buy_items'),
    url(
        '^buy_item/(?P<pk>\d+)/(?P<item_pk>\d+)$',
        views.BuyItemView.as_view(),
        name='buy_item'),
    url(
        '^sell_item/(?P<pk>\d+)/(?P<item_pk>\d+)$',
        views.SellItemView.as_view(),
        name='sell_item'),

    url(
        '^xhr_buy_weapon_modifications/(?P<pk>\d+)$',
        views.XhrBuyWeaponModView.as_view(),
        name='xhr_buy_weapon_modifications'),
    url(
        '^buy_weapon_modification/(?P<pk>\d+)/(?P<weapon_modification_pk>\d+)/(?P<weapon_pk>\d+)$',
        views.BuyWeaponModificationView.as_view(),
        name='buy_weapon_modification'),

]
