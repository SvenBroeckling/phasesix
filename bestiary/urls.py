from django.urls import path

from bestiary import views

app_name = 'bestiary'

urlpatterns = [
    path('list/', views.FoeListView.as_view(), name='list'),
    path('detail/<int:pk>', views.FoeDetailView.as_view(), name='detail'),
]
