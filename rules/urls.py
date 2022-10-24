from django.urls import path

from rules import views

app_name = 'rules'

urlpatterns = [
    path('templates/', views.TemplateListView.as_view(), name='template_list'),
]
