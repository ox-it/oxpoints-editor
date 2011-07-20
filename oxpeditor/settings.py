# Django settings for oxpeditor project.
import ConfigParser
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

config = ConfigParser.ConfigParser()
config.read(os.path.join(ROOT, 'config.ini'))

CONFIG_PATH = os.path.join(ROOT, config.get('main', 'config'))

DEBUG = config.get('main', 'debug', 'false') == 'true'
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('OxPoints RT Queue', 'oxpoints@oucs.ox.ac.uk'),
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'oxpeditor'   # Or path to database file if using sqlite3.
DATABASE_USER = 'oxpeditor'             # Not used with sqlite3.
DATABASE_PASSWORD = config.get('database', 'password')         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

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

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/site-media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin-media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'u4y$mvh=+g^twh+ropxb1djfyojkvgjwvogxb)-h70p)a9uotl'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'oxpeditor.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "oxpeditor.core.context_processors.core",
)


INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'mptt',
    'oxpeditor.core',
    'oxpeditor.utils',
    'oxpeditor.webauth',
    # Uncomment the next line to enable the admin:
)

REPO_PATH = os.path.join(ROOT, 'oxpoints-data')
SERVER_NAME = 'oxpoints.oucs.ox.ac.uk'

LOGIN_URL = '/webauth/login/'

AUTHENTICATION_BACKENDS = (
    'oxpeditor.webauth.backends.WebauthBackend',
    'django.contrib.auth.backends.ModelBackend',
)

SVN_USER = config.get('svn', 'user')
SVN_PASSWORD = config.get('svn', 'password')

EMAIL_HOST = 'smtp.ox.ac.uk'
EMAIL_PORT = 587
EMAIL_HOST_USER = config.get('email', 'user')
EMAIL_HOST_PASSWORD = config.get('email', 'password')
SERVER_EMAIL = 'oxpoints@opendata.nsms.ox.ac.uk'
DEFAULT_FROM_EMAIL = 'oxpoints@oucs.ox.ac.uk'

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 36000

