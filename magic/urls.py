from django.conf.urls import url

from magic import views

app_name = 'magic'

urlpatterns = [
    url('^spell/list/$', views.BaseSpellListView.as_view(), name='basespell_list'),
    url(r'^spell/detail/(?P<pk>\d+)$', views.BaseSpellDetailView.as_view(), name='basespell_detail'),
]
