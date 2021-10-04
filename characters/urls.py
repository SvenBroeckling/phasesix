from django.conf.urls import url

from characters import views

app_name = 'characters'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^detail/(?P<pk>\d+)$', views.CharacterDetailView.as_view(), name='detail'),
    url(r'^list/$', views.CharacterListView.as_view(), name='list'),
    url(r'^xhr_delete/(?P<pk>\d+)$', views.XhrDeleteCharacterView.as_view(), name='xhr_delete'),

    url(r'^dice_json/$', views.DiceJsonView.as_view(), name='dice_json'),

    url(
        r'^xhr_detail_sidebar/(?P<pk>\d+)/(?P<model_name>[A-Za-z_]+)/(?P<sidebar_name>[a-z_]+)$',
        views.XhrSidebarView.as_view(),
        name='xhr_detail_sidebar'),
    url(
        r'^xhr_detail_fragment/(?P<pk>\d+)/(?P<model_name>[A-Za-z_]+)/(?P<fragment_name>[a-z_]+)$',
        views.XhrDetailFragmentView.as_view(),
        name='xhr_detail_fragment'),

    # health
    url(
        r'^health/(?P<pk>\d+)/(?P<mode>\w+)/$',
        views.CharacterModifyHealthView.as_view(),
        name='modify_health'),
    url(
        r'^rest/(?P<pk>\d+)/$',
        views.XhrCharacterRestView.as_view(),
        name='xhr_rest'),

    # magic
    url(
        r'^arcana/(?P<pk>\d+)/(?P<mode>\w+)/$',
        views.CharacterModifyArcanaView.as_view(),
        name='modify_arcana'),
    url(
        r'^spell/cast/(?P<pk>\d+)/$',
        views.CharacterCastSpellView.as_view(),
        name='cast_spell'),

    # dice
    url(
        r'^dice/(?P<pk>\d+)/(?P<mode>\w+)/$',
        views.CharacterModifyDiceView.as_view(),
        name='modify_dice'),

    # Weapons
    url(
        r'^attack/(?P<characterweapon_pk>\d+)/(?P<weapon_attackmode_pk>\d+)/$',
        views.CharacterAttackView.as_view(),
        name='attack'),
    url(
        r'^reload/(?P<characterweapon_pk>\d+)/$',
        views.CharacterReloadView.as_view(),
        name='reload'),

    # horror
    url(
        r'^stress/(?P<pk>\d+)/(?P<mode>\w+)/$',
        views.CharacterModifyStressView.as_view(),
        name='modify_stress'),

    # new character
    url(r'^new/$', views.CreateCharacterView.as_view(), name='create_character'),
    url(
        r'^new/data/(?P<extension_pk>\d+)/$',
        views.CreateCharacterDataView.as_view(),
        name='create_character_data'),

    # constructed
    url(
        r'^new/constructed/(?P<pk>\d+)$',
        views.CreateCharacterConstructedView.as_view(),
        name='create_character_constructed'),
    url(
        r'^new/constructed/add_template/(?P<pk>\d+)$',
        views.XhrConstructedAddTemplateView.as_view(),
        name='xhr_constructed_add_template'),
    url(
        r'^new/constructed/preview/(?P<pk>\d+)$',
        views.XhrCreateCharacterPreviewView.as_view(),
        name='xhr_create_character_preview'),
    url(
        r'^new/constructed/remove_template/(?P<pk>\d+)$',
        views.XhrConstructedRemoveTemplateView.as_view(),
        name='xhr_constructed_remove_template'),

    # Images etc
    url(
        r'^change_image/(?P<pk>\d+)$',
        views.ChangeImageView.as_view(),
        name='change_image'),

    # reputation and status
    url(
        r'^xhr_reputation/(?P<pk>\d+)$',
        views.XhrReputationView.as_view(),
        name='xhr_reputation'),
    url(
        r'^xhr_status_effects/change/(?P<pk>\d+)$',
        views.XhrCharacterStatusEffectsChangeView.as_view(),
        name='xhr_status_effects_change'),

    # weapons
    url(
        r'^xhr_add_weapons/(?P<pk>\d+)$',
        views.XhrAddWeaponsView.as_view(),
        name='xhr_add_weapons'),
    url(
        r'^add_weapon/(?P<pk>\d+)/(?P<weapon_pk>\d+)$',
        views.AddWeaponView.as_view(),
        name='add_weapon'),
    url(
        r'^xhr_remove_weapon/(?P<pk>\d+)/(?P<weapon_pk>\d+)$',
        views.XhrRemoveWeaponView.as_view(),
        name='xhr_remove_weapon'),
    url(
        r'^xhr_remove_weapon_modification/(?P<pk>\d+)/(?P<weapon_pk>\d+)/(?P<weapon_modification_pk>\d+)$',
        views.XhrRemoveWeaponModificationView.as_view(),
        name='xhr_remove_weapon_modification'),
    url(
        r'^xhr_weapon_condition/(?P<pk>\d+)/(?P<weapon_pk>\d+)(?P<mode>\w+)/$',
        views.XhrWeaponConditionView.as_view(),
        name='xhr_weapon_condition'),

    # riot gear
    url(
        r'^xhr_add_riot_gear/(?P<pk>\d+)$',
        views.XhrAddRiotGearView.as_view(),
        name='xhr_add_riot_gear'),
    url(
        r'^add_riot_gear/(?P<pk>\d+)/(?P<riot_gear_pk>\d+)$',
        views.AddRiotGearView.as_view(),
        name='add_riot_gear'),
    url(
        r'^xhr_remove_riot_gear/(?P<pk>\d+)/(?P<riot_gear_pk>\d+)$',
        views.XhrRemoveRiotGearView.as_view(),
        name='xhr_remove_riot_gear'),
    url(
        r'^xhr_riot_gear_condition/(?P<pk>\d+)/(?P<riot_gear_pk>\d+)(?P<mode>\w+)/$',
        views.XhrRiotGearConditionView.as_view(),
        name='xhr_riot_gear_condition'),

    # items
    url(
        r'^xhr_add_items/(?P<pk>\d+)$',
        views.XhrAddItemsView.as_view(),
        name='xhr_add_items'),
    url(
        r'^add_item/(?P<pk>\d+)/(?P<item_pk>\d+)$',
        views.AddItemView.as_view(),
        name='add_item'),
    url(
        r'^xhr_remove_item/(?P<pk>\d+)/(?P<item_pk>\d+)$',
        views.XhrRemoveItemView.as_view(),
        name='xhr_remove_item'),

    # weapon modifications
    url(
        r'^xhr_add_weapon_modifications/(?P<pk>\d+)$',
        views.XhrAddWeaponModView.as_view(),
        name='xhr_add_weapon_modifications'),
    url(
        r'^add_weapon_modification/(?P<pk>\d+)/(?P<weapon_modification_pk>\d+)/(?P<weapon_pk>\d+)$',
        views.AddWeaponModificationView.as_view(),
        name='add_weapon_modification'),

    # magic
    url(
        r'^xhr_add_spell/(?P<pk>\d+)$',
        views.XhrAddSpellView.as_view(),
        name='xhr_add_spell'),
]
