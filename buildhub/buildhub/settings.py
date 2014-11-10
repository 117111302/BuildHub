"""
Django settings for buildhub project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import urlparse
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'qh0o)6ifrcla2085e8hyfn(hgzymw5==jxt55!ji@a&p867_#4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/'

ALLOWED_HOSTS = []

# SSH key path

GERRIT_SSH_KEY_PATH = os.path.expanduser('~/.ssh')

# GitHub Client
GITHUB_API = 'https://api.github.com/'
BACKEND_SERVER = 'http://buildhub.ngrok.com'
CLIENT_ID = 'c24112678dd3df9d297a'
CLIENT_SECRET = '91173ae4a4274d2a5602d188dcc0f1cc9078be04'
OAUTH_URL = 'https://github.com/login/oauth/authorize'
REDIRECT_URI = urlparse.urljoin(BACKEND_SERVER, '/auth/')

# Jenkins
#JENKINS_URL = 'http://tzs.bj.intel.com/ci/'
JENKINS_URL = 'http://nemo-precise.bj.intel.com:8080/'
JENKINS_USER = 'junchunx'
JENKINS_PASS = 'tizen2.0'
JENKINS_JOB = 'Yocto-Builder'

#JENKINS_URL = 'http://tzjenkins-test.fi.intel.com/robot'
#JENKINS_USER = 'root'
#JENKINS_PASS = 'namtriv7'
#JENKINS_JOB = 'buildhub_test'

# Mongodb

MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017
MONGODB_NAME = 'buildhub'
MONGODB_COLLECTION = 'groups'

# Badge
BADGE_URL = 'http://img.shields.io/badge/build-%s-%s.svg'

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'buildhub.urls'

WSGI_APPLICATION = 'buildhub.wsgi.application'


# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
    '/var/www/static/',
)

TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]
