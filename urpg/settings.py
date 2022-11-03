import os

from django.urls import reverse_lazy
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(BASE_DIR, '.env'))

BASE_URL = os.environ['BASE_URL']
SECRET_KEY = os.environ['SECRET_KEY']

ADMINS = [('Sven', 'sven@broeckling.de')]

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 365  # 1 year

DEBUG = True if os.environ['DEBUG'] == 'True' else False
DEBUG_DISCORD = False

ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(',')
ASGI_APPLICATION = "urpg.asgi.application"
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(os.environ['REDIS_HOST'], int(os.environ['REDIS_PORT']))],
        },
    },
}

ACCOUNT_ACTIVATION_DAYS = 7
LOGIN_URL = reverse_lazy('login')
CSRF_COOKIE_MASKED = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'daphne',
    'channels',
    'django.contrib.staticfiles',
    'django_registration',
    'django_extensions',
    'reversion',
    'sorl.thumbnail',
    'bootstrap4',
    'compressor',
    'gmtools',
    'armory',
    'bestiary',
    'world',
    'homebrew',
    'rules',
    'characters',
    'rulebook',
    'forum',
    'magic',
    'horror',
    'campaigns',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'urpg.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATICFILE_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]

WSGI_APPLICATION = 'urpg.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['DATABASE_NAME'],
        'USER': os.environ['DATABASE_USER'],
        'PASSWORD': os.environ['DATABASE_PASSWORD'],
        'HOST': os.environ['DATABASE_HOST'],
        'PORT': int(os.environ['DATABASE_PORT']),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'de'

gettext = lambda s: s  # dummy ugettext function, as django's docs say

LANGUAGES = (
    ('de', gettext('German')),
    ('en', gettext('English')),
)
LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]

DEFAULT_FROM_EMAIL = 'game@phasesix.org'
EMAIL_HOST = os.environ['EMAIL_HOST']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_PASSWORD']
EMAIL_HOST_USER = os.environ['EMAIL_USER']

TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static_files')
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]

COMPRESS_ENABLED = not DEBUG
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media_files')

RULEBOOK_ROOT = os.path.join(BASE_DIR, 'rulebook', 'static', 'rulebook')

LOGIN_REDIRECT_URL = "/"
