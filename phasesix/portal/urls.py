from django.urls import path
from django.views.decorators.cache import cache_page

from portal import views

app_name = "portal"

urlpatterns = [
    path("profile/<int:pk>", views.ProfileView.as_view(), name="profile"),
    path(
        "profile/upload_image",
        views.ProfileUploadImageView.as_view(),
        name="upload_image",
    ),
    path("sidebar/search", views.SidebarSearchView.as_view(), name="search"),
    path(
        "wrapup/<int:pk>/<int:year>",
        cache_page(60 * 30)(views.YearlyWrapUpView.as_view()),
        name="wrapup",
    ),
    path("xhr/search", views.XhrSearchResultsView.as_view(), name="xhr_search_results"),
]
