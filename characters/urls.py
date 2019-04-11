from django.conf.urls import url

from characters import views

app_name = 'characters'

urlpatterns = [
    url('^$', views.IndexView.as_view(), name='index'),
    url('^detail/(?P<pk>\d+)$', views.CharacterDetailView.as_view(), name='detail'),
    url('^list/$', views.CharacterListView.as_view(), name='list'),

    url(
        r'^xhr_detail_fragment/(?P<pk>\d+)/(?P<fragment_name>[a-z_]+)$',
        views.XhrDetailFragmentView.as_view(),
        name='xhr_detail_fragment'),

    url(
        '^health/(?P<pk>\d+)/(?P<mode>\w+)/$',
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

    # Images etc
    url(
        '^xhr_change_image/(?P<pk>\d+)$',
        views.XhrChangeImageView.as_view(),
        name='xhr_change_image'),
    url(
        '^change_image/(?P<pk>\d+)$',
        views.ChangeImageView.as_view(),
        name='change_image'),

    # gear
    url(
        '^xhr_add_weapons/(?P<pk>\d+)$',
        views.XhrAddWeaponsView.as_view(),
        name='xhr_add_weapons'),

    url(
        '^add_weapon/(?P<pk>\d+)/(?P<weapon_pk>\d+)$',
        views.AddWeaponView.as_view(),
        name='add_weapon'),
    url(
        '^xhr_remove_weapon/(?P<pk>\d+)/(?P<weapon_pk>\d+)$',
        views.XhrRemoveWeaponView.as_view(),
        name='xhr_remove_weapon'),
    url(
        '^xhr_damage_weapon/(?P<pk>\d+)/(?P<weapon_pk>\d+)$',
        views.XhrDamageWeaponView.as_view(),
        name='xhr_damage_weapon'),

    url(
        '^xhr_add_riot_gear/(?P<pk>\d+)$',
        views.XhrAddRiotGearView.as_view(),
        name='xhr_add_riot_gear'),
    url(
        '^add_riot_gear/(?P<pk>\d+)/(?P<riot_gear_pk>\d+)$',
        views.AddRiotGearView.as_view(),
        name='add_riot_gear'),
    url(
        '^xhr_remove_riot_gear/(?P<pk>\d+)/(?P<riot_gear_pk>\d+)$',
        views.XhrRemoveRiotGearView.as_view(),
        name='xhr_remove_riot_gear'),
    url(
        '^xhr_damage_riot_gear/(?P<pk>\d+)/(?P<riot_gear_pk>\d+)$',
        views.XhrDamageRiotGearView.as_view(),
        name='xhr_damage_riot_gear'),

    url(
        '^xhr_add_items/(?P<pk>\d+)$',
        views.XhrAddItemsView.as_view(),
        name='xhr_add_items'),
    url(
        '^add_item/(?P<pk>\d+)/(?P<item_pk>\d+)$',
        views.AddItemView.as_view(),
        name='add_item'),
    url(
        '^xhr_remove_item/(?P<pk>\d+)/(?P<item_pk>\d+)$',
        views.XhrRemoveItemView.as_view(),
        name='xhr_remove_item'),

    url(
        '^xhr_add_weapon_modifications/(?P<pk>\d+)$',
        views.XhrAddWeaponModView.as_view(),
        name='xhr_add_weapon_modifications'),
    url(
        '^add_weapon_modification/(?P<pk>\d+)/(?P<weapon_modification_pk>\d+)/(?P<weapon_pk>\d+)$',
        views.AddWeaponModificationView.as_view(),
        name='add_weapon_modification'),

]
