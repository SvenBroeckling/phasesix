import os
from pathlib import Path

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))

BASE_URL = os.environ["BASE_URL"]
SECRET_KEY = os.environ["SECRET_KEY"]

ADMINS = [("Sven", "sven@broeckling.de")]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 365  # 1 year

DEBUG = True if os.environ["DEBUG"] == "True" else False
DEBUG_TOOLBAR = True if os.environ.get("DEBUG_TOOLBAR", "False") == "True" else False
DEBUG_DISCORD = False

ALLOWED_HOSTS = os.environ["ALLOWED_HOSTS"].split(",")
CSRF_TRUSTED_ORIGINS = [f"https://{a}" for a in ALLOWED_HOSTS]


ASGI_APPLICATION = "phasesix.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.environ["REDIS_HOST"], int(os.environ["REDIS_PORT"]))],
        },
    },
}

ACCOUNT_ACTIVATION_DAYS = 7
LOGIN_URL = reverse_lazy("login")

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.humanize",
    "daphne",
    "channels",
    "django.contrib.staticfiles",
    "django_registration",
    "django_extensions",
    "django_bootstrap5",
    "cachalot",
    "reversion",
    "django_htmx",
    "sorl.thumbnail",
    "compressor",
    "characters",
    "rulebook",
    "forum",
    "portal",
    "gmtools",
    "armory",
    "worlds",
    "homebrew",
    "rules",
    "magic",
    "horror",
    "pantheon",
    "body_modifications",
    "campaigns",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "worlds.middleware.WorldFromDomainNameMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if DEBUG:
    INTERNAL_IPS = ["127.0.0.1"]
    if DEBUG_TOOLBAR:
        INSTALLED_APPS.append("debug_toolbar")
        MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
        DEBUG_TOOLBAR_PANELS = [
            "debug_toolbar.panels.history.HistoryPanel",
            "debug_toolbar.panels.versions.VersionsPanel",
            "debug_toolbar.panels.timer.TimerPanel",
            "debug_toolbar.panels.settings.SettingsPanel",
            "debug_toolbar.panels.headers.HeadersPanel",
            "debug_toolbar.panels.request.RequestPanel",
            "debug_toolbar.panels.sql.SQLPanel",
            "debug_toolbar.panels.staticfiles.StaticFilesPanel",
            "debug_toolbar.panels.templates.TemplatesPanel",
            "debug_toolbar.panels.cache.CachePanel",
            "debug_toolbar.panels.signals.SignalsPanel",
            "debug_toolbar.panels.redirects.RedirectsPanel",
            "debug_toolbar.panels.profiling.ProfilingPanel",
            "cachalot.panels.CachalotPanel",
        ]

ROOT_URLCONF = "phasesix.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "worlds.context_processors.brand_information",
            ],
        },
    },
]

STATICFILE_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
]

WSGI_APPLICATION = "phasesix.wsgi.application"

if os.environ.get("DATABASE_ENGINE", None) is None:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": os.environ["DATABASE_ENGINE"],
            "NAME": os.environ["DATABASE_NAME"],
            "USER": os.environ["DATABASE_USER"],
            "PASSWORD": os.environ["DATABASE_PASSWORD"],
            "HOST": os.environ["DATABASE_HOST"],
            "PORT": int(os.environ["DATABASE_PORT"]),
        }
    }

SILENCED_SYSTEM_CHECKS = [
    "cachalot.W001",
    "cachalot.W002",
]  # cachalot complaining about wrong redis cache, but uses it
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{os.environ['REDIS_HOST']}:{os.environ['REDIS_PORT']}",
        "KEY_PREFIX": "phasesix_cache",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "de"

gettext = lambda s: s  # dummy ugettext function, as django's docs say

LANGUAGES = (
    ("de", gettext("German")),
    ("en", gettext("English")),
)
LOCALE_PATHS = [os.path.join(BASE_DIR, "locale")]

DEFAULT_FROM_EMAIL = os.environ["DEFAULT_FROM_EMAIL"]
SERVER_EMAIL = os.environ["DEFAULT_FROM_EMAIL"]
EMAIL_HOST = os.environ["EMAIL_HOST"]
EMAIL_HOST_PASSWORD = os.environ["EMAIL_PASSWORD"]
EMAIL_HOST_USER = os.environ["EMAIL_USER"]
EMAIL_PORT = int(os.environ["EMAIL_PORT"])
EMAIL_USE_TLS = os.environ["EMAIL_USE_TLS"] == "True"

TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = os.environ.get("STATIC_URL", "static/")
STATIC_ROOT = BASE_DIR / os.environ.get("STATIC_ROOT_RELATIVE", "static_files")
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
]

COMPRESS_ENABLED = not DEBUG
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)

MEDIA_URL = os.environ.get("MEDIA_URL", "/media/")
MEDIA_ROOT = BASE_DIR / os.environ.get("MEDIA_ROOT_RELATIVE", "media_files")

RULEBOOK_ROOT = os.path.join(BASE_DIR, "rulebook", "static", "rulebook")

LOGIN_REDIRECT_URL = "/"

UNFOLD = {
    "SITE_TITLE": "Phase Six",
    "SITE_HEADER": "Phase Six",
    "SITE_ICON": {
        "light": "/static/img/phsaesix_logo_2.png",
        "dark": "/static/img/phasesix_logo_2.png",
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("Characters and Campaigns"),
                "separator": True,
                "collapsible": False,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "people",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": _("Characters"),
                        "icon": "people",
                        "link": reverse_lazy("admin:characters_character_changelist"),
                    },
                    {
                        "title": _("Campaigns"),
                        "icon": "people",
                        "link": reverse_lazy("admin:campaigns_campaign_changelist"),
                    },
                ],
            },
            {
                "title": _("Armory"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Items"),
                        "icon": "people",
                        "link": reverse_lazy("admin:armory_item_changelist"),
                    },
                    {
                        "title": _("Riot Gear"),
                        "icon": "people",
                        "link": reverse_lazy("admin:armory_riotgear_changelist"),
                    },
                    {
                        "title": _("Currency Maps"),
                        "icon": "people",
                        "link": reverse_lazy("admin:armory_currencymap_changelist"),
                    },
                    {
                        "title": _("Weapons"),
                        "icon": "people",
                        "link": reverse_lazy("admin:armory_weapon_changelist"),
                    },
                ],
            },
            {
                "title": _("Extensions"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Body Modifications"),
                        "icon": "people",
                        "link": reverse_lazy(
                            "admin:body_modifications_bodymodification_changelist"
                        ),
                    },
                    {
                        "title": _("Horror Quirks"),
                        "icon": "people",
                        "link": reverse_lazy("admin:horror_quirk_changelist"),
                    },
                    {
                        "title": _("Spells"),
                        "icon": "people",
                        "link": reverse_lazy("admin:magic_basespell_changelist"),
                    },
                    {
                        "title": _("Dieties"),
                        "icon": "people",
                        "link": reverse_lazy("admin:pantheon_entity_changelist"),
                    },
                ],
            },
            {
                "title": _("Rules"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Extensions"),
                        "icon": "people",
                        "link": reverse_lazy("admin:rules_extension_changelist"),
                    },
                    {
                        "title": _("Book Chapters"),
                        "icon": "people",
                        "link": reverse_lazy("admin:rulebook_chapter_changelist"),
                    },
                    {
                        "title": _("Lineages"),
                        "icon": "people",
                        "link": reverse_lazy("admin:rules_lineage_changelist"),
                    },
                    {
                        "title": _("Character templates"),
                        "icon": "people",
                        "link": reverse_lazy("admin:rules_template_changelist"),
                    },
                ],
            },
            {
                "title": _("Worlds"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Languages"),
                        "icon": "people",
                        "link": reverse_lazy("admin:worlds_language_changelist"),
                    },
                    {
                        "title": _("Worlds"),
                        "icon": "people",
                        "link": reverse_lazy("admin:worlds_world_changelist"),
                    },
                    {
                        "title": _("Wiki Pages"),
                        "icon": "people",
                        "link": reverse_lazy("admin:worlds_wikipage_changelist"),
                    },
                ],
            },
        ],
    },
}
