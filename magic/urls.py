from django.conf.urls import url

from magic import views

app_name = 'magic'

urlpatterns = [
    url(
        '^xhr_spell/(?P<pk>\d+)$',
        views.XhrSpellView.as_view(),
        name='xhr_spell'),
    url(
        '^xhr_spell_cost/$',
        views.XhrSpellCostView.as_view(),
        name='xhr_spell_cost'),
    url(
        '^xhr_spell_flavour/$',
        views.XhrSpellFlavourOptionsView.as_view(),
        name='xhr_spell_flavour'),
    url(
        '^xhr_spell_summary/$',
        views.XhrSpellSummaryView.as_view(),
        name='xhr_spell_summary'),
]
