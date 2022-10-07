from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from campaigns import views

app_name = 'campaigns'

urlpatterns = [
    url(r'^list/$', login_required(views.CampaignListView.as_view()), name='list'),
    url(r'^create/$', login_required(views.CampaignCreateView.as_view()), name='create'),

    url(r'^detail/(?P<pk>\d+)$', views.CampaignDetailView.as_view(), name='detail'),
    url(r'^detail/(?P<pk>\d+)/invite/(?P<hash>\w+)$', views.CampaignDetailView.as_view(), name='detail'),
    url(r'^detail/settings/(?P<pk>\d+)$', views.SaveSettingsView.as_view(), name='save_settings'),

    url(
        r'^xhr_campaign_fragment/(?P<pk>\d+)/(?P<fragment_template>[a-z_]+)$',
        views.XhrCampaignFragmentView.as_view(),
        name='xhr_campaign_fragment'),

    url(
        r'^remove_character/(?P<pk>\d+)/(?P<character_pk>\d+)$',
        views.XhrRemoveCharacterView.as_view(),
        name='xhr_remove_character'),
    url(
        r'^switch_npc/(?P<pk>\d+)/(?P<character_pk>\d+)$',
        views.XhrSwitchCharacterNPCView.as_view(),
        name='xhr_switch_npc'),

    url(
        r'^sidebar/(?P<pk>\d+)/(?P<sidebar_template>[a-z_]+)$',
        views.XhrSidebarView.as_view(),
        name='xhr_sidebar'),
    url(
        r'^sidebar/settings/(?P<pk>\d+)/(?P<sidebar_template>[a-z_]+)$',
        views.XhrSettingsSidebarView.as_view(),
        name='xhr_settings_sidebar'),
    url(
        r'^sidebar/character/(?P<pk>\d+)/(?P<sidebar_template>[a-z_]+)$',
        views.XhrCharacterSidebarView.as_view(),
        name='xhr_character_sidebar'),
]
