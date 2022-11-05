from django.urls import path

from worlds import views

app_name = 'worlds'

urlpatterns = [
    path('<int:pk>', views.DetailView.as_view(), name='detail'),
]
