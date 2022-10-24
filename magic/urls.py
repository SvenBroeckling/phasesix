from django.urls import path

from magic import views

app_name = 'magic'

urlpatterns = [
    path('spell/list/', views.BaseSpellListView.as_view(), name='basespell_list'),
    path('spell/detail/<int:pk>', views.BaseSpellDetailView.as_view(), name='basespell_detail'),
]
