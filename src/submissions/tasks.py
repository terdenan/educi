from django.conf import settings

from config.celery import app
from submissions.utils.downloader import (
    DownloadManager, UploadedSourcesStrategy, DownloadRepositoryStrategy
)


@app.task
def perform_submission(submission_id):
    from submissions.models import Submission
    submission = Submission.objects.get(pk=submission_id)
    submission.run()


@app.task
def prepare_sources(submission_id, download_type):
    from submissions.models import Submission

    submission = Submission.objects.get(pk=submission_id)
    downloader = DownloadManager()

    if download_type == Submission.STRATEGY_SOURCES:
        downloader.strategy = UploadedSourcesStrategy(submission)
    elif download_type == Submission.STRATEGY_REPOSITORY:
        downloader.strategy = DownloadRepositoryStrategy(submission)

    downloader.download()
