from django.contrib.auth.decorators import login_required
from django.urls import path

from campaigns import views

app_name = 'campaigns'

urlpatterns = [
    path('list/', login_required(views.CampaignListView.as_view()), name='list'),

    path('new/', login_required(views.CreateCampaignView.as_view()), name='create'),
    path(
        'new/<int:world_pk>/',
        views.CreateCampaignEpochView.as_view(),
        name='create_epoch'),
    path(
        'new/<int:world_pk>/<int:epoch_pk>)/',
        views.CreateCampaignExtensionsView.as_view(),
        name='create_extensions'),
    path(
        'new/data/<int:world_pk>/<int:epoch_pk>/',
        views.CreateCampaignDataView.as_view(),
        name='create_data'),

    path('detail/<int:pk>', views.CampaignDetailView.as_view(), name='detail'),
    path('detail/<int:pk>/invite/<hash>', views.CampaignDetailView.as_view(), name='detail'),
    path('detail/settings/<int:pk>', views.SaveSettingsView.as_view(), name='save_settings'),

    path(
        'xhr_campaign_fragment/<int:pk>/<fragment_template>',
        views.XhrCampaignFragmentView.as_view(),
        name='xhr_campaign_fragment'),

    path(
        'remove_character/<int:pk>/<int:character_pk>',
        views.XhrRemoveCharacterView.as_view(),
        name='xhr_remove_character'),
    path(
        'switch_npc/<int:pk>/<int:character_pk>',
        views.XhrSwitchCharacterNPCView.as_view(),
        name='xhr_switch_npc'),

    path(
        'add_foe/<int:pk>/<int:wiki_page_pk>',
        views.XhrAddFoeToCampaignView.as_view(),
        name='xhr_add_foe'),
    path(
        'remove_foe/<int:pk>/<int:foe_pk>',
        views.XhrRemoveFoeView.as_view(),
        name='xhr_remove_foe'),

    path(
        'sidebar/<int:pk>/<sidebar_template>',
        views.XhrSidebarView.as_view(),
        name='xhr_sidebar'),
    path(
        'sidebar/settings/<int:pk>/<sidebar_template>',
        views.XhrSettingsSidebarView.as_view(),
        name='xhr_settings_sidebar'),
    path(
        'sidebar/character/<int:pk>/<sidebar_template>',
        views.XhrCharacterSidebarView.as_view(),
        name='xhr_character_sidebar'),
    path(
        'sidebar/foe/<int:pk>/<sidebar_template>',
        views.XhrFoeSidebarView.as_view(),
        name='xhr_foe_sidebar'),
    path(
        'game_log/<int:campaign_pk>',
        views.XhrCampaignGameLogView.as_view(),
        name='xhr_game_log'),
]
