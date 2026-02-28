import os
from pathlib import Path

import yaml

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load YAML configuration
with open(BASE_DIR / 'mdviewer.yaml') as _f:
    YAML_CONFIG = yaml.safe_load(_f)

# SECURITY WARNING: keep the secret key used in production secret!
try:
    SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
except KeyError:
    raise RuntimeError("Set the DJANGO_SECRET_KEY environment variable before starting the application.")

DEBUG = YAML_CONFIG['debug']
ALLOWED_HOSTS = YAML_CONFIG['allowed_hosts']

# Application definition
INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'rest_framework',
    'library',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'library.middleware.ContentSecurityPolicyMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mdviewer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'mdviewer.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / YAML_CONFIG['database_path'],
    }
}

REST_FRAMEWORK = {
    # No auth or user model — disable DRF's default AnonymousUser import,
    # which pulls in django.contrib.auth and django.contrib.contenttypes.
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/minute',
        'library_list': '60/minute',
        'library_create': '10/minute',
        'library_detail': '60/minute',
        'library_update': '20/minute',
        'library_delete': '20/minute',
        'library_stats': '30/minute',
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Security settings
SECURE_CONTENT_TYPE_NOSNIFF = True                          # sets X-Content-Type-Options: nosniff
X_FRAME_OPTIONS = 'DENY'                                    # sets X-Frame-Options: DENY
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'  # sets Referrer-Policy header

# Reject oversized request bodies before they reach the view layer.
# Add headroom above max_upload_bytes to account for request envelope overhead.
DATA_UPLOAD_MAX_MEMORY_SIZE = YAML_CONFIG['max_upload_bytes'] + 100_000

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': str(BASE_DIR / YAML_CONFIG['log_directory'] / 'mdviewer.log'),
            'formatter': 'standard',
        },
    },
    'loggers': {
        'library': {
            'handlers': ['file'],
            'level': YAML_CONFIG['log_level'],
            'propagate': False,
        },
    },
}
