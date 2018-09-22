from django.conf.urls import url

from rules import views

app_name = 'rules'

urlpatterns = [
    url('^templates/$', views.TemplateListView.as_view(), name='template_list'),
]
