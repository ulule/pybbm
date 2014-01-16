import django

DEBUG = True
TEMPLATE_DEBUG = DEBUG

import os

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'testdb.sqlite',
    }
}

LANGUAGE_CODE = 'en-us'
SITE_ID = 1

STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

SECRET_KEY = 'qd@j3*it@3j2cgc#7t@m)^r1bnc53uam7o6u_+x$f5w3$b@3ix'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'pybb.contrib.profiles.middleware.PybbMiddleware',
    'pybb.contrib.ban.middleware.PybbBanMiddleware',
)

ROOT_URLCONF = 'pybb.tests.urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'pybb',
    'pybb.contrib.profiles',
    'pybb.contrib.mentions',
    'pybb.contrib.quotes',
    'pybb.contrib.smilies',
    'pybb.contrib.reports',
    'pybb.contrib.ban',
    'sorl.thumbnail',
    'pytils',
    'registration',
    'guardian',
    'django.contrib.humanize',
)

STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.static',
    'pybb.context_processors.processor',
)

AUTH_PROFILE_MODULE = 'pybb.Profile'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

PYBB_ATTACHMENT_ENABLE = True

PYBB_SMILIES_USE_CACHE = False

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.eggs.Loader',
    'django.template.loaders.app_directories.Loader',
)

ANONYMOUS_USER_ID = -1

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

PYBB_BBCODE_MARKUP_FORMATTERS = (
    ('quote', ('pybb.contrib.quotes.formatters.quote', None)),
    ('mention', ('pybb.contrib.mentions.formatters.mention', None)),
)

PYBB_POST_CREATE_VIEW = 'pybb.contrib.quotes.views.PostCreateView'

PYBB_MARKUP_PREPROCESSORS = (
    'pybb.sanitizer.BleachProcessor',
    'pybb.contrib.mentions.processors.MentionProcessor',
    'pybb.contrib.smilies.processors.SmileyProcessor',
)

PYBB_NOTIFICATION_ENABLE = True

PYBB_DUPLICATE_TOPIC_SLUG_ALLOWED = False

PYBB_BAN_CHECK_TIMEOUT = 0

PYBB_BODY_CLEANERS = [
    'pybb.util.rstrip_str',
    'pybb.util.filter_blanks',
]

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'public_forums',
    },
}

if django.VERSION <= (1, 6):
    TEST_RUNNER = 'discover_runner.DiscoverRunner'

AUTH_PROFILE_MODULE = 'pybb.Profile'

MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')
