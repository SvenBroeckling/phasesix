from django.conf.urls import url

from characters import views

app_name = 'characters'

urlpatterns = [
    url('^$', views.IndexView.as_view(), name='index'),
    # url('^new/$', login_required(views.NewCharacterView.as_view()), name='new_character'),
    # url('^detail/(?P<pk>\d+)$', views.CharacterDetailView.as_view(), name='detail'),
]
