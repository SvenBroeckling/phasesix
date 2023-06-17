from django.urls import path

from worlds import views

app_name = "worlds"

urlpatterns = [
    path(
        "foe_list",
        views.WikiPageWithGameValuesView.as_view(),
        name="wiki_page_with_game_values",
    ),
    path("<str:slug>", views.WorldDetailView.as_view(), name="detail"),
    path(
        "<str:world_slug>/<str:slug>",
        views.WikiPageDetailView.as_view(),
        name="wiki_page",
    ),
    path(
        "<str:world_slug>/<str:slug>/edit",
        views.WikiPageEditTextView.as_view(),
        name="edit_text",
    ),
    path(
        "xhr_create/page/<int:world_pk>",
        views.XhrCreateWikiPageView.as_view(),
        name="xhr_create_wiki_page",
    ),
    path(
        "xhr_create/page/<int:world_pk>/<int:parent_pk>",
        views.XhrCreateWikiPageView.as_view(),
        name="xhr_create_wiki_page",
    ),
    # Sidebars
    path(
        r"sidebar/<str:slug>/<str:sidebar_template>/",
        views.XhrSidebarView.as_view(),
        name="xhr_sidebar",
    ),
    path(
        r"world_sidebar/<str:slug>/<str:sidebar_template>",
        views.XhrWorldSortSubPagesSidebarView.as_view(),
        name="xhr_world_sort_sidebar",
    ),
    path(
        r"wikipage_sidebar/<str:slug>/<str:sidebar_template>",
        views.XhrWikiPageSortSubPagesSidebarView.as_view(),
        name="xhr_wiki_page_sort_sidebar",
    ),
    path(
        "xhr_update_wiki_page_sort_order/<int:pk>/<str:model>",
        views.XhrUpdateItemSortOrderView.as_view(),
        name="xhr_update_wiki_page_sort_order",
    ),
    path(
        r"search_links/<str:world_slug>/",
        views.XhrSearchLinksView.as_view(),
        name="xhr_search_links",
    ),
    path(
        r"upload_image/<str:slug>/",
        views.XhrUploadImageView.as_view(),
        name="xhr_upload_image",
    ),
    path(
        r"additional_images/<str:slug>/",
        views.XhrAdditionalImagesView.as_view(),
        name="xhr_additional_images",
    ),
    path(
        r"xhr_auto_tag/<int:pk>/", views.XhrAutoTagView.as_view(), name="xhr_auto_tag"
    ),
]
