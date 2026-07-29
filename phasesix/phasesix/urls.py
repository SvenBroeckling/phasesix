from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path, re_path
from django.views.generic import TemplateView
from django.views.static import serve
from characters.feeds import LatestModifiedAdmin, LatestNewAdmin
from portal.forms import CustomRegistrationForm
from portal.views import (
    ActivationCompleteView,
    ActivationView,
    IndexView,
    PasswordResetView,
    RegistrationCompleteView,
    RegistrationView,
)

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("feeds/new_admin/", LatestNewAdmin()),
    path("feeds/modified_admin/", LatestModifiedAdmin()),
    path("api/", include("api.urls", namespace="api")),
    path("", include("characters.urls", namespace="characters")),
    path(
        "essential/",
        include("essential_characters.urls", namespace="essential_characters"),
    ),
    path("admin/", admin.site.urls),
    path(
        "contact/", TemplateView.as_view(template_name="contact.html"), name="contact"
    ),
    path("events/", include("eventstream.urls", namespace="eventstream")),
    path("campaigns/", include("campaigns.urls", namespace="campaigns")),
    path("magic/", include("magic.urls", namespace="magic")),
    path("forum/", include("forum.urls", namespace="forum")),
    path("rulebook/", include("rulebook.urls", namespace="rulebook")),
    path("homebrew/", include("homebrew.urls", namespace="homebrew")),
    path("rules/", include("rules.urls", namespace="rules")),
    path("armory/", include("armory.urls", namespace="armory")),
    path(
        "body_modifications/",
        include("body_modifications.urls", namespace="body_modifications"),
    ),
    path("world/", include("worlds.urls", namespace="world")),
    path("curators_desk/", include("curators_desk.urls", namespace="curators_desk")),
    path("plots/", include("plots.urls", namespace="plots")),
    path("", include("partypad.urls", namespace="partypad")),
    path(
        "accounts/password_reset/",
        PasswordResetView.as_view(),
        name="password_reset",
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    path(
        "accounts/register/",
        RegistrationView.as_view(form_class=CustomRegistrationForm),
        name="django_registration_register",
    ),
    path(
        "accounts/activate/",
        ActivationView.as_view(),
        name="django_registration_activate",
    ),
    path(
        "accounts/activate/complete/",
        ActivationCompleteView.as_view(),
        name="django_registration_activation_complete",
    ),
    path(
        "accounts/register/complete/",
        RegistrationCompleteView.as_view(),
        name="django_registration_complete",
    ),
    path("accounts/", include("django_registration.backends.activation.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("portal/", include("portal.urls", namespace="portal")),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})
    ]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    if settings.DEBUG_TOOLBAR:
        urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
