
from django.conf.urls import include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path
from django.views.static import serve
from django.views.generic import TemplateView

from characters.feeds import LatestNewAdmin, LatestModifiedAdmin

urlpatterns = [
    path('feeds/new_admin/', LatestNewAdmin()),
    path('feeds/modified_admin/', LatestModifiedAdmin()),

    path('', include('characters.urls', namespace='characters')),
    path('admin/', admin.site.urls),
    path('contact/', TemplateView.as_view(template_name="contact.html"), name="contact"),
    path('campaigns/', include('campaigns.urls', namespace='campaigns')),
    path('magic/', include('magic.urls', namespace='magic')),
    path('forum/', include('forum.urls', namespace='forum')),
    path('rulebook/', include('rulebook.urls', namespace='rulebook')),
    path('bestiary/', include('bestiary.urls', namespace='bestiary')),
    path('homebrew/', include('homebrew.urls', namespace='homebrew')),
    path('rules/', include('rules.urls', namespace='rules')),
    path('armory/', include('armory.urls', namespace='armory')),
    path('gmtools/', include('gmtools.urls', namespace='gmtools')),
    path('you/', include('django.contrib.auth.urls')),
    path('you/', include('django_registration.backends.activation.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
]

if settings.DEBUG:
    urlpatterns += [re_path(r'^media/(?P<path>.*)$', serve,
                        {'document_root': settings.MEDIA_ROOT})]
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
