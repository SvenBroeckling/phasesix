from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from campaigns import views

app_name = 'campaigns'

urlpatterns = [
    url(r'^list/$', login_required(views.CampaignListView.as_view()), name='list'),
    url(r'^create/$', login_required(views.CampaignCreateView.as_view()), name='create'),
    url(r'^detail/(?P<pk>\d+)$', views.CampaignDetailView.as_view(), name='detail'),
]
