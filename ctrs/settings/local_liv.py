from .base import *  # noqa

ALLOWED_HOSTS = ['ctrs.kdl.kcl.ac.uk']

INTERNAL_IPS = INTERNAL_IPS + ['']

DATABASES = {
    'default': {
        'ENGINE': db_engine,
        'NAME': 'app_ctrs_liv',
        'USER': 'app_ctrs',
        'PASSWORD': '',
        'HOST': ''
    },
}

SECRET_KEY = ''
