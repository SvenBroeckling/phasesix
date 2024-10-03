from django.contrib.auth.decorators import login_required
from django.urls import path

from portal import views

app_name = "portal"

urlpatterns = [
    path("profile/", login_required(views.ProfileView.as_view()), name="profile"),
    path("sidebar/search/", views.SidebarSearchView.as_view(), name="search"),
    path(
        "wrapup/<int:pk>",
        views.YearlyWrapUpView.as_view(),
        name="wrapup",
    ),
    path(
        "xhr/search/", views.XhrSearchResultsView.as_view(), name="xhr_search_results"
    ),
]
