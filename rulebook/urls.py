from django.conf.urls import url

from rulebook import views

app_name = 'rulebook'

urlpatterns = [
    url('^$', views.IndexView.as_view(), name='index'),
    # url('^detail/(?P<pk>\d+)$', views.CharacterDetailView.as_view(), name='detail'),
]
