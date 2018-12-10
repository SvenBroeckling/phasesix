
from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views.static import serve
from django.views.generic import TemplateView

from characters.feeds import LatestNewAdmin

urlpatterns = [
    url(r'feeds/new_admin/$', LatestNewAdmin()),
    url(r'feeds/modified_admin/$', LatestNewAdmin()),

    url(r'^admin/', admin.site.urls),
    url(r'^contact/', TemplateView.as_view(template_name="characters/contact.html"), name="contact"),
    url(r'^', include('characters.urls', namespace='characters')),
    url(r'forum/', include('forum.urls', namespace='forum')),
    url(r'rulebook/', include('rulebook.urls', namespace='rulebook')),
    url(r'rules/', include('rules.urls', namespace='rules')),
    url(r'gmtools/', include('gmtools.urls', namespace='gmtools')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('django_registration.backends.activation.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
]

if settings.DEBUG:
    urlpatterns += [url(r'^media/(?P<path>.*)$', serve,
                        {'document_root': settings.MEDIA_ROOT})]
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
