from django.conf.urls import url

from gmtools import views

app_name = 'gmtools'

urlpatterns = [
    url('^combat_sim/$', views.CombatSimView.as_view(), name='combat_sim'),
]
