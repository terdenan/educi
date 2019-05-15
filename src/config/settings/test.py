from .base import *

DEBUG = True

ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', cast=int),
    }
}

CELERY_BROKER_URL = config('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = 'django-db'

# Solving unit testing problem with celery
# http://docs.celeryproject.org/projects/django-celery/en/2.4/cookbook/unit-testing.html
TEST_RUNNER = 'config.test_runner.CeleryTestSuiteRunner'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media_test')
HOST_MEDIA_ROOT = config('HOST_MEDIA_ROOT')
