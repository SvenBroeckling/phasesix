from django.urls import path

from forum import views

app_name = 'forum'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('board/<int:pk>/', views.BoardDetailView.as_view(), name="board_detail"),
    path('thread/<int:pk>/', views.ThreadDetailView.as_view(), name="thread_detail"),
    path('subscribe/<str:mode>/', views.SubscribeView.as_view(), name='subscribe'),
]
