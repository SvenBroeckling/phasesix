from django.conf.urls import url

from magic import views

app_name = 'magic'

urlpatterns = [
    url(
        '^xhr_spell/(?P<pk>\d+)$',
        views.XhrSpellView.as_view(),
        name='xhr_spell'),
]
