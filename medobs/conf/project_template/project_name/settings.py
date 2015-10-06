"""
Django settings for MEDOBS.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


### DEBUG ###
DEBUG = True


### EMAILS ###
ADMINS = (
	('Administrator MEDOBS', 'medobs@email.em'),
)
MANAGERS = ADMINS

DEFAULT_FROM_EMAIL = 'no-reply@email.em'


### DATABASE ###
DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.sqlite3',
		'NAME': os.path.join(BASE_DIR, 'medobs.sqlite3'),
	}
}


### SECRET KEY ###
SECRET_KEY = '{{ secret_key }}'


### HOSTS ###
ALLOWED_HOSTS = ['*']


### PATHS ###
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

MEDIA_URL = '/media/'
MEDIA_ROOT =  os.path.join(BASE_DIR, 'media/')


### INTERNATIONALIZATION ###
LANGUAGES = (
	('en-us', u'English'),
	('sk', u'Slovak'),
)
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Bratislava'
USE_I18N = True
USE_L10N = True
USE_TZ = False


### OTHER ###
SITE_ID = 1

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
	'localflavor',
	'medobs.reservations',
	'django.contrib.admin',
)

TEMPLATES = [{
	'BACKEND': 'django.template.backends.django.DjangoTemplates',
	'DIRS': [],
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
		],
	},
}]

ROOT_URLCONF = '{{ project_name }}.urls'
WSGI_APPLICATION = '{{ project_name }}.wsgi.application'


### CUSTOM SETTINGS ###
try:
	from settings_custom import *
except ImportError:
	pass


# vim: set ts=4 sts=4 sw=4 noet:
