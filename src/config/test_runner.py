from django.conf import settings
from django.test.runner import DiscoverRunner

from celery import current_app


class CeleryTestSuiteRunner(DiscoverRunner):

    def setup_test_environment(self, **kwargs):
        current_app.conf.CELERY_TASK_ALWAYS_EAGER = True
        settings.CELERY_TASK_ALWAYS_EAGER = True
        super(CeleryTestSuiteRunner, self).setup_test_environment(**kwargs)
