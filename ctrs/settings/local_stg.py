from .base import *  # noqa

ALLOWED_HOSTS = ['ctrs-stg.kdl.kcl.ac.uk']

CACHE_REDIS_DATABASE = '1'
CACHES['default']['LOCATION'] = 'redis://127.0.0.1:6379/' + CACHE_REDIS_DATABASE  # noqa

INTERNAL_IPS = INTERNAL_IPS + ['']
ALLOWED_HOSTS = ['']

DATABASES = {
    'default': {
        'ENGINE': db_engine,
        'NAME': 'app_ctrs_stg',
        'USER': 'app_ctrs',
        'PASSWORD': '',
        'HOST': ''
    },
}

SECRET_KEY = ''
