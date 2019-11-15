from django.conf.urls import url

from rulebook import views

app_name = 'rulebook'

urlpatterns = [
    url('^chapter/(?P<pk>\d+)$', views.ChapterDetailView.as_view(), name='detail'),
]
