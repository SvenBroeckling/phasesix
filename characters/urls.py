from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from characters import views

app_name = 'characters'

urlpatterns = [
    url('^$', views.IndexView.as_view(), name='index'),
    url('^new/$', login_required(views.RandomCharacterView.as_view()), name='random_character'),
    url('^detail/(?P<pk>\d+)$', views.CharacterDetailView.as_view(), name='detail'),
]
