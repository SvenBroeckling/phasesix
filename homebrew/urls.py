from django.conf.urls import url

from homebrew import views

app_name = 'homebrew'

urlpatterns = [
    url('^$', views.IndexView.as_view(), name='index'),
]
