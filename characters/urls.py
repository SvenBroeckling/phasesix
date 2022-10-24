from django.urls import path

from characters import views

app_name = 'characters'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('detail/<int:pk>', views.CharacterDetailView.as_view(), name='detail'),
    path('list/', views.CharacterListView.as_view(), name='list'),
    path('xhr_delete/<int:pk>', views.XhrDeleteCharacterView.as_view(), name='xhr_delete'),

    # Sidebars
    path(
        r'sidebar_character/<int:pk>/<str:sidebar_template>/',
        views.XhrCharacterSidebarView.as_view(),
        name='xhr_character_sidebar'),
    path(
        r'sidebar_characteritem/<int:pk>/<str:sidebar_template>/',
        views.XhrCharacterItemSidebarView.as_view(),
        name='xhr_characteritem_sidebar'),
    path(
        r'sidebar_characterskill/<int:pk>/<str:sidebar_template>/',
        views.XhrCharacterSkillSidebarView.as_view(),
        name='xhr_characterskill_sidebar'),
    path(
        r'sidebar_characterspell/<int:pk>/<str:sidebar_template>/',
        views.XhrCharacterSpellSidebarView.as_view(),
        name='xhr_characterspell_sidebar'),
    path(
        r'sidebar_characterweapon/<int:pk>/<str:sidebar_template>/',
        views.XhrCharacterWeaponSidebarView.as_view(),
        name='xhr_characterweapon_sidebar'),
    path(
        r'sidebar_characterriotgear/<int:pk>/<str:sidebar_template>/',
        views.XhrCharacterRiotGearSidebarView.as_view(),
        name='xhr_characterriotgear_sidebar'),
    path(
        r'sidebar_characterattribute/<int:pk>/<str:sidebar_template>/',
        views.XhrCharacterAttributeSidebarView.as_view(),
        name='xhr_characterattribute_sidebar'),
    path(
        r'sidebar_characterknowledge/<int:pk>/<str:sidebar_template>/<int:knowledge_pk>/',
        views.XhrCharacterKnowledgeSidebarView.as_view(),
        name='xhr_characterknowledge_sidebar'),
    path(
        r'sidebar_charactertemplateshadow/<int:pk>/<str:sidebar_template>/',
        views.XhrCharacterTemplateShadowSidebarView.as_view(),
        name='xhr_charactertemplateshadow_sidebar'),
    path(
        r'sidebar_characternote/<int:pk>/<str:sidebar_template>/',
        views.XhrCharacterNoteSidebarView.as_view(),
        name='xhr_characternote_sidebar'),

    path(
        'xhr_detail_fragment/<int:pk>/<fragment_template>',
        views.XhrDetailFragmentView.as_view(),
        name='xhr_detail_fragment'),

    # health
    path(
        'health/<int:pk>/<mode>/',
        views.CharacterModifyHealthView.as_view(),
        name='modify_health'),
    path(
        'rest/<int:pk>/',
        views.XhrCharacterRestView.as_view(),
        name='xhr_rest'),

    # magic
    path(
        'arcana/<int:pk>/<mode>/',
        views.CharacterModifyArcanaView.as_view(),
        name='modify_arcana'),
    path(
        'xhr_add_spell/<int:pk>',
        views.XhrAddSpellView.as_view(),
        name='xhr_add_spell'),
    path(
        'xhr_remove_spell/<int:pk>',
        views.XhrRemoveSpellView.as_view(),
        name='xhr_remove_spell'),
    path(
        'spell/cast/<int:pk>/',
        views.CharacterCastSpellView.as_view(),
        name='cast_spell'),
    path(
        'xhr_add_spell_template/<int:pk>',
        views.XhrAddSpellTemplateView.as_view(),
        name='xhr_add_spell_template'),
    path(
        'add_spell_template/<int:pk>/<int:spell_template_pk>/<int:character_spell_pk>',
        views.AddSpellTemplateView.as_view(),
        name='add_spell_template'),

    # dice
    path(
        'dice/<int:pk>/<mode>/',
        views.CharacterModifyDiceView.as_view(),
        name='modify_dice'),

    # Weapons
    path(
        'attack/<int:characterweapon_pk>/<int:weapon_attackmode_pk>/',
        views.CharacterAttackView.as_view(),
        name='attack'),
    path(
        'reload/<int:characterweapon_pk>/',
        views.CharacterReloadView.as_view(),
        name='reload'),

    # horror
    path(
        'stress/<int:pk>/<mode>/',
        views.CharacterModifyStressView.as_view(),
        name='modify_stress'),
    path(
        'choose_quirk/<int:pk>/',
        views.XhrAddQuirkView.as_view(),
        name='xhr_choose_quirk'),
    path(
        'add_quirk/<int:pk>/<int:quirk_pk>',
        views.AddQuirkView.as_view(),
        name='add_quirk'),

    # new character
    path('new/', views.CreateCharacterView.as_view(), name='create_character'),
    path(
        'new/<int:world_pk>/',
        views.CreateCharacterEpochView.as_view(),
        name='create_character_epoch'),
    path(
        'new/<int:world_pk>/<int:epoch_pk>/',
        views.CreateCharacterExtensionsView.as_view(),
        name='create_character_extensions'),
    path(
        'new/data/<int:world_pk>/<int:epoch_pk>/',
        views.CreateCharacterDataView.as_view(),
        name='create_character_data'),
    path(
        'new/data/<int:epoch_pk>/<int:world_pk>/<int:campaign_pk>/<hash>/<type>/',
        views.CreateCharacterDataView.as_view(),
        name='create_character_data'),
    path(
        'new/random_npc/<int:epoch_pk>/<int:world_pk>/<int:campaign_pk>/<hash>/<type>/',
        views.CreateRandomNPCView.as_view(),
        name='create_random_npc'),

    # constructed
    path(
        'new/constructed/<int:pk>',
        views.CreateCharacterConstructedView.as_view(),
        name='create_character_constructed'),
    path(
        'new/constructed/add_template/<int:pk>',
        views.XhrConstructedAddTemplateView.as_view(),
        name='xhr_constructed_add_template'),
    path(
        'new/constructed/preview/<int:pk>',
        views.XhrCreateCharacterPreviewView.as_view(),
        name='xhr_create_character_preview'),
    path(
        'new/constructed/remove_template/<int:pk>',
        views.XhrConstructedRemoveTemplateView.as_view(),
        name='xhr_constructed_remove_template'),

    # Images etc
    path(
        'change_image/<int:pk>',
        views.ChangeImageView.as_view(),
        name='change_image'),

    # reputation and status
    path(
        'xhr_reputation/<int:pk>',
        views.XhrReputationView.as_view(),
        name='xhr_reputation'),
    path(
        'xhr_status_effects/change/<int:pk>/<int:status_effect_pk>/<mode>/',
        views.XhrCharacterStatusEffectsChangeView.as_view(),
        name='xhr_status_effects_change'),

    # weapons
    path(
        'xhr_add_weapons/<int:pk>',
        views.XhrAddWeaponsView.as_view(),
        name='xhr_add_weapons'),
    path(
        'add_weapon/<int:pk>/<int:weapon_pk>',
        views.AddWeaponView.as_view(),
        name='add_weapon'),
    path(
        'xhr_remove_weapon/<int:pk>/<int:weapon_pk>',
        views.XhrRemoveWeaponView.as_view(),
        name='xhr_remove_weapon'),
    path(
        'xhr_remove_weapon_modification/<int:pk>/<int:weapon_pk>/<int:weapon_modification_pk>',
        views.XhrRemoveWeaponModificationView.as_view(),
        name='xhr_remove_weapon_modification'),
    path(
        'xhr_weapon_condition/<int:pk>/<int:weapon_pk>/<mode>/',
        views.XhrWeaponConditionView.as_view(),
        name='xhr_weapon_condition'),

    # riot gear
    path(
        'xhr_add_riot_gear/<int:pk>',
        views.XhrAddRiotGearView.as_view(),
        name='xhr_add_riot_gear'),
    path(
        'add_riot_gear/<int:pk>/<int:riot_gear_pk>',
        views.AddRiotGearView.as_view(),
        name='add_riot_gear'),
    path(
        'xhr_remove_riot_gear/<int:pk>/<int:riot_gear_pk>',
        views.XhrRemoveRiotGearView.as_view(),
        name='xhr_remove_riot_gear'),
    path(
        'xhr_riot_gear_condition/<int:pk>/<int:riot_gear_pk><mode>/',
        views.XhrRiotGearConditionView.as_view(),
        name='xhr_riot_gear_condition'),

    # items
    path(
        'xhr_add_items/<int:pk>',
        views.XhrAddItemsView.as_view(),
        name='xhr_add_items'),
    path(
        'add_item/<int:pk>/<int:item_pk>',
        views.AddItemView.as_view(),
        name='add_item'),
    path(
        'xhr_modify_item/<int:pk>/<int:item_pk>/<mode>',
        views.XhrModifyItemView.as_view(),
        name='xhr_modify_item'),
    path(
        'xhr_update_item_sort_order/<int:pk>',
        views.XhrUpdateItemSortOrderView.as_view(),
        name='xhr_update_item_sort_order'),
    path(
        'modify_currency/<int:pk>',
        views.XhrModifyCurrencyView.as_view(),
        name='xhr_modify_currency'),
    path(
        'xhr_put_into/<int:pk>/<int:item_pk>/<int:container_pk>',
        views.XhrPutIntoView.as_view(),
        name='xhr_put_into'),
    path(
        'xhr_put_into/<int:pk>/<int:item_pk>',
        views.XhrPutIntoView.as_view(),
        name='xhr_put_into'),

    # weapon modifications
    path(
        'xhr_add_weapon_modifications/<int:pk>',
        views.XhrAddWeaponModView.as_view(),
        name='xhr_add_weapon_modifications'),
    path(
        'add_weapon_modification/<int:pk>/<int:weapon_modification_pk>/<int:character_weapon_pk>',
        views.AddWeaponModificationView.as_view(),
        name='add_weapon_modification'),

    # Notes
    path(
        'xhr_create_note/<int:pk>',
        views.XhrCreateNoteView.as_view(),
        name='xhr_create_note'),
    path(
        'xhr_update_note/<int:pk>/<int:note_pk>',
        views.XhrUpdateNoteView.as_view(),
        name='xhr_update_note'),
    path(
        'xhr_delete_note/<int:pk>/<int:note_pk>',
        views.XhrDeleteNoteView.as_view(),
        name='xhr_delete_note'),
]
