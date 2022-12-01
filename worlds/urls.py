from django.urls import path

from worlds import views

app_name = 'worlds'

urlpatterns = [
    path('<str:slug>', views.WorldDetailView.as_view(), name='detail'),

    path(
        '<str:world_slug>/<str:slug>',
        views.WikiPageDetailView.as_view(),
        name='wiki_page'),
    path(
        '<str:world_slug>/<str:slug>/edit',
        views.WikiPageEditTextView.as_view(),
        name='edit_text'),

    path(
        'xhr_create/page/<int:world_pk>',
        views.XhrCreateWikiPageView.as_view(),
        name='xhr_create_wiki_page'),
    path(
        'xhr_create/page/<int:world_pk>/<int:parent_pk>',
        views.XhrCreateWikiPageView.as_view(),
        name='xhr_create_wiki_page'),

    # Sidebars
    path(
        r'sidebar/<str:slug>/<str:sidebar_template>/',
        views.XhrSidebarView.as_view(),
        name='xhr_sidebar'),
    path(
        r'search_links/<str:world_slug>/',
        views.XhrSearchLinksView.as_view(),
        name='xhr_search_links'),
    path(
        r'upload_image/<str:slug>/',
        views.XhrUploadImageView.as_view(),
        name='xhr_upload_image'),
    path(
        r'additional_images/<str:slug>/',
        views.XhrAdditionalImagesView.as_view(),
        name='xhr_additional_images'),
    path(
        r'xhr_modal_image/<int:pk>/',
        views.XhrModalImageView.as_view(),
        name='xhr_modal_image'),

]
