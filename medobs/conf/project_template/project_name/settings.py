"""
Django settings for Medobs.
"""

import os

import ldap
from django_auth_ldap.config import LDAPSearch, PosixGroupType


BASE_DIR = os.path.dirname(os.path.dirname(__file__))


### DEBUG ###
DEBUG = False


### INTERNATIONALIZATION ###
LANGUAGES = (
	('sk', u'Slovak'),
	('en-us', u'English'),
)
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Bratislava'
USE_I18N = True
USE_L10N = True
USE_TZ = True
# jQuery UI datepicker localization file name
# The localization files are also available in the UI svn:
# http://jquery-ui.googlecode.com/svn/trunk/ui/i18n/
# Base path is STATIC_ROOT.
# Example: "js/i18n/jquery.ui.datepicker-sk.js"
DATEPICKER_I18N_FILE = "js/i18n/jquery.ui.datepicker-sk.js"


### LDAP AUTHENTICATION ###
AUTHENTICATION_BACKENDS = (
	'django_auth_ldap.backend.LDAPBackend',
	'django.contrib.auth.backends.ModelBackend',
)
AUTH_LDAP_START_TLS = True

AUTH_LDAP_USER_SEARCH = LDAPSearch("ou=people,dc=gis,dc=lab", ldap.SCOPE_SUBTREE, "(uid=%(user)s)")
# or perhaps:
#AUTH_LDAP_USER_DN_TEMPLATE = "uid=%(user)s,ou=people,dc=gis,dc=lab"

AUTH_LDAP_GROUP_SEARCH = LDAPSearch("ou=groups,dc=gis,dc=lab", ldap.SCOPE_SUBTREE, "(objectClass=posixGroup)")
AUTH_LDAP_GROUP_TYPE = PosixGroupType()
AUTH_LDAP_REQUIRE_GROUP = "cn=gislabusers,ou=groups,dc=gis,dc=lab"

AUTH_LDAP_USER_ATTR_MAP = {
	"first_name": "givenName",
	"last_name": "sn",
	"email": "mail"
}
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
	"is_active": "cn=gislabusers,ou=groups,dc=gis,dc=lab",
	"is_staff": "cn=gislabadmins,ou=groups,dc=gis,dc=lab",
	"is_superuser": "cn=gislabadmins,ou=groups,dc=gis,dc=lab"
}

AUTH_LDAP_GLOBAL_OPTIONS = {
	ldap.OPT_X_TLS_REQUIRE_CERT: False,
}

AUTH_LDAP_ALWAYS_UPDATE_USER = True
AUTH_LDAP_FIND_GROUP_PERMS = True
AUTH_LDAP_CACHE_GROUPS = True
AUTH_LDAP_GROUP_CACHE_TIMEOUT = 3600


### OTHER ###
SITE_ID = 1
ALLOWED_HOSTS = ['*']

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

MEDIA_URL = '/media/'

if os.path.exists('/storage/applications/medobs/media'):
	MEDIA_ROOT = '/storage/applications/medobs/media'
else:
	MEDIA_ROOT =  os.path.join(BASE_DIR, 'media/')

MIDDLEWARE_CLASSES = (
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.locale.LocaleMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
)

INSTALLED_APPS = (
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.sites',
	'django.contrib.staticfiles',
	'django.contrib.messages',
	'django.contrib.admin',
	'localflavor',
	'medobs.reservations',
)

if DEBUG:
	INSTALLED_APPS += (
		"django.contrib.admindocs",
	)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
        	'debug': DEBUG,
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
				'medobs.context_processors.version',
				'medobs.context_processors.datepicker_i18n_file',
            ],
        },
    },
]

ROOT_URLCONF = '{{ project_name }}.urls'
WSGI_APPLICATION = '{{ project_name }}.wsgi.application'

#LOGIN_URL = '/login/'
#AUTH_USER_MODEL = 'viewer.GislabUser'


# import secret settings
try:
	from settings_secret import *
except ImportError:
	pass


# vim: set syntax=sh ts=4 sts=4 sw=4 noet