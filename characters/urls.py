from django.conf.urls import url

from characters import views

app_name = 'characters'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^detail/(?P<pk>\d+)$', views.CharacterDetailView.as_view(), name='detail'),
    url(r'^list/$', views.CharacterListView.as_view(), name='list'),

    url(
        r'^xhr_detail_fragment/(?P<pk>\d+)/(?P<fragment_name>[a-z_]+)$',
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

    # horror
    url(
        r'^stress/(?P<pk>\d+)/(?P<mode>\w+)/$',
        views.CharacterModifyStressView.as_view(),
        name='modify_stress'),

    # new character
    url(r'^new/$', views.CreateCharacterView.as_view(), name='create_character'),
    url(
        r'^new/data/(?P<extension_pk>\d+)/(?P<mode>\w+)/$',
        views.CreateCharacterDataView.as_view(),
        name='create_character_data'),

    # draft
    url(r'^new/draft/(?P<pk>\d+)$', views.CreateCharacterDraftView.as_view(), name='create_character_draft'),
    url(
        r'^new/draft/preview/(?P<pk>\d+)$',
        views.XhrCreateCharacterPreviewView.as_view(),
        name='xhr_create_character_preview'),
    url(
        r'^new/draft/templates/(?P<pk>\d+)$',
        views.XhrDraftPreviewSelectedTemplatesView.as_view(),
        name='xhr_draft_preview_selected_templates'),
    url(
        r'^new/draft/add_template/(?P<pk>\d+)$',
        views.XhrDraftAddTemplateView.as_view(),
        name='xhr_draft_add_template'),

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
        r'^new/constructed/remove_template/(?P<pk>\d+)$',
        views.XhrConstructedRemoveTemplateView.as_view(),
        name='xhr_constructed_remove_template'),

    # Images etc
    url(
        r'^xhr_change_image/(?P<pk>\d+)$',
        views.XhrChangeImageView.as_view(),
        name='xhr_change_image'),
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
        r'^xhr_status_effects/(?P<pk>\d+)$',
        views.XhrCharacterStatusEffectsView.as_view(),
        name='xhr_status_effects'),
    url(
        r'^xhr_status_effects/change/(?P<pk>\d+)$',
        views.XhrCharacterStatusEffectsChangeView.as_view(),
        name='xhr_status_effects_change'),

    # gear
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
        r'^xhr_damage_weapon/(?P<pk>\d+)/(?P<weapon_pk>\d+)$',
        views.XhrDamageWeaponView.as_view(),
        name='xhr_damage_weapon'),

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
        r'^xhr_damage_riot_gear/(?P<pk>\d+)/(?P<riot_gear_pk>\d+)$',
        views.XhrDamageRiotGearView.as_view(),
        name='xhr_damage_riot_gear'),

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

    url(
        r'^xhr_add_weapon_modifications/(?P<pk>\d+)$',
        views.XhrAddWeaponModView.as_view(),
        name='xhr_add_weapon_modifications'),
    url(
        r'^add_weapon_modification/(?P<pk>\d+)/(?P<weapon_modification_pk>\d+)/(?P<weapon_pk>\d+)$',
        views.AddWeaponModificationView.as_view(),
        name='add_weapon_modification'),

]
