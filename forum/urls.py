from django.conf.urls import url

from forum import views

app_name = 'forum'

urlpatterns = [
    url('^$', views.IndexView.as_view(), name='index'),
]
