from django.urls import path
from django.views.decorators.cache import cache_page

from portal import views

app_name = "portal"

urlpatterns = [
    path("profile/<slug:slug>", views.ProfileView.as_view(), name="profile"),
    path("sidebar/search", views.SidebarSearchView.as_view(), name="search"),
    path(
        "wrapup/<int:pk>/<int:year>",
        views.YearlyWrapUpView.as_view(),
        name="wrapup",
    ),
    path("xhr/search", views.XhrSearchResultsView.as_view(), name="xhr_search_results"),
]
