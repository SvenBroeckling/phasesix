from django.conf.urls import url

from rulebook import views

app_name = 'rulebook'

urlpatterns = [
    url(r'^chapter/(?P<pk>\d+)$', views.ChapterDetailView.as_view(), name='detail'),
    url(r'^book/(?P<pk>\d+)/pdf$', views.BookPDFView.as_view(), name='book_pdf'),
]
