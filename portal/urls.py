from django.urls import path

from portal import views

app_name = 'portal'

urlpatterns = [
    path('sidebar/search/', views.SidebarSearchView.as_view(), name='search'),
    path('xhr/search/', views.XhrSearchResultsView.as_view(), name='xhr_search_results'),
]
