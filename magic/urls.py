from django.urls import path

from magic import views

app_name = 'magic'

urlpatterns = [
    path('spell/origins/', views.SpellOriginView.as_view(), name='spell_origin_list'),
    path('spell/list/<int:origin_pk>', views.BaseSpellListView.as_view(), name='basespell_list'),
    path('spell/detail/<int:pk>', views.BaseSpellDetailView.as_view(), name='basespell_detail'),
]
