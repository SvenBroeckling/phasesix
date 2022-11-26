from django.urls import path

from worlds import views

app_name = 'worlds'

urlpatterns = [
    path('<int:pk>', views.WorldDetailView.as_view(), name='detail'),

    path('<str:slug>', views.WikiPageDetailView.as_view(), name='wiki_page'),

    path(
        'xhr_create/page/<int:world_pk>',
        views.XhrCreateWikiPageView.as_view(),
        name='xhr_create_wiki_page'),
    path(
        'xhr_create/page/<int:world_pk>/<int:parent_pk>',
        views.XhrCreateWikiPageView.as_view(),
        name='xhr_create_wiki_page'),
]
