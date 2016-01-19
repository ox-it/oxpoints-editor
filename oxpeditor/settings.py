# Django settings for oxpeditor project.
import ConfigParser
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

DEBUG = os.environ.get('DEBUG') == 'true'
TEMPLATE_DEBUG = DEBUG

FROM_ADDRESS = os.environ['FROM_ADDRESS']
NOTIFY_ADDRESS = os.environ['NOTIFY_ADDRESS']
STATIC_ROOT = os.environ['STATIC_ROOT']
PREFIX = os.environ.get('PREFIX', '/')

ADMINS = (
    ('OxPoints RT Queue', NOTIFY_ADDRESS),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['DATABASE_NAME'],
   },
}

ALLOWED_HOSTS = ['*']

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

CSRF_COOKIE_PATH = PREFIX
CSRF_COOKIE_SECURE = not DEBUG
FORCE_SCRIPT_NAME = PREFIX

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

STATIC_URL = PREFIX + 'static/'

try:
    SECRET_KEY = os.environ['SECRET_KEY']
except KeyError:
    with open(os.environ['SECRET_KEY_FILE']) as f:
        SECRET_KEY = f.read()

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'oxpeditor.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.static",
    "django.contrib.auth.context_processors.auth",
    "oxpeditor.core.context_processors.core",
)


INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'mptt',
    'oxpeditor.core',
    'oxpeditor.webauth',
    # Uncomment the next line to enable the admin:
)

REPO_PATH = os.environ['OXPOINTS_DATA_CHECKOUT_DIR']
SERVER_NAME = 'oxpoints.oucs.ox.ac.uk'

LOGIN_URL = PREFIX + 'webauth/login/'

AUTHENTICATION_BACKENDS = (
    'oxpeditor.webauth.backends.WebauthBackend',
    'django.contrib.auth.backends.ModelBackend',
)

SVN_USER = os.environ['SVN_USER']
try:
    SVN_PASSWORD = os.environ['SVN_PASSWORD']
except KeyError:
    with open(os.environ['SVN_PASSWORD_FILE']) as f:
        SVN_PASSWORD = f.read()

EMAIL_HOST = os.environ['SMTP_SERVER']
SERVER_EMAIL = FROM_ADDRESS
DEFAULT_FROM_EMAIL = NOTIFY_ADDRESS

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 36000

