from django.conf.urls import url

from magic import views

app_name = 'magic'

urlpatterns = [
    url('^spell/$', views.BaseSpellListView.as_view(), name='basespell_list'),
]
