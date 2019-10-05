from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from campaigns import views

app_name = 'campaigns'

urlpatterns = [
    url(r'^list/$', login_required(views.CampaignListView.as_view()), name='list'),
    url(r'^create/$', login_required(views.CampaignCreateView.as_view()), name='create'),
    url(r'^detail/(?P<pk>\d+)$', login_required(views.CampaignDetailView.as_view()), name='detail'),
    url(r'^update/(?P<pk>\d+)$', login_required(views.CampaignUpdateView.as_view()), name='update'),
    url(r'^scenes/(?P<pk>\d+)$', login_required(views.CampaignScenesView.as_view()), name='scenes'),
    url(r'^invitation/(?P<pk>\d+)/(?P<hash>.+)$', login_required(views.CampaignInvitationView.as_view()), name='invitation'),
]
