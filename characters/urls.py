from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from characters import views

app_name = 'characters'

urlpatterns = [
    url('^$', views.IndexView.as_view(), name='index'),
    url('^detail/(?P<pk>\d+)$', views.CharacterDetailView.as_view(), name='detail'),
    url('^list/$', views.CharacterListView.as_view(), name='list'),

    url(
        '^new/data/(?P<pk>\d+)/(?P<mode>\w+)/$',
        views.CharacterModifyHealthView.as_view(),
        name='modify_health'),

    # health

    # new character
    url('^new/$', views.CreateCharacterView.as_view(), name='create_character'),
    url(
        '^new/data/(?P<extension_pk>\d+)/(?P<mode>\w+)/$',
        views.CreateCharacterDataView.as_view(),
        name='create_character_data'),

    # draft
    url('^new/draft/(?P<pk>\d+)$', views.CreateCharacterDraftView.as_view(), name='create_character_draft'),
    url(
        '^new/draft/preview/(?P<pk>\d+)$',
        views.XhrCreateCharacterPreviewView.as_view(),
        name='xhr_create_character_preview'),
    url(
        '^new/draft/templates/(?P<pk>\d+)$',
        views.XhrDraftPreviewSelectedTemplatesView.as_view(),
        name='xhr_draft_preview_selected_templates'),
    url(
        '^new/draft/add_template/(?P<pk>\d+)$',
        views.XhrDraftAddTemplateView.as_view(),
        name='xhr_draft_add_template'),

    # constructed
    url(
        '^new/constructed/(?P<pk>\d+)$',
        views.CreateCharacterConstructedView.as_view(),
        name='create_character_constructed'),
    url(
        '^new/constructed/add_template/(?P<pk>\d+)$',
        views.XhrConstructedAddTemplateView.as_view(),
        name='xhr_constructed_add_template'),
    url(
        '^new/constructed/remove_template/(?P<pk>\d+)$',
        views.XhrConstructedRemoveTemplateView.as_view(),
        name='xhr_constructed_remove_template'),

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
