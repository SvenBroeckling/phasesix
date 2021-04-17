from django.conf.urls import url

from bestiary import views

app_name = 'bestiary'

urlpatterns = [
    url(r'^list/$', views.FoeListView.as_view(), name='list'),
    url(r'^detail/(?P<pk>\d+)$', views.FoeDetailView.as_view(), name='detail'),
]
