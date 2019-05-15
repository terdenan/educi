import os
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

from celery import chain

from courses.models import Assignment
from submissions.utils import random_temporary_dir
from submissions.utils import docker
from submissions.tasks import perform_submission, prepare_sources

User = get_user_model()


class Submission(models.Model):
    PROCESSING = 0
    PERFORMED = 1
    FAILED = 2

    STATUS_CHOICES = (
        (PROCESSING, 'processing'),
        (PERFORMED, 'performed'),
        (FAILED, 'failed'),
    )

    STRATEGY_SOURCES = 'sources'
    STRATEGY_REPOSITORY = 'repository'

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviewed_submissions', null=True)
    repo_url = models.CharField(max_length=255, blank=True)
    branch = models.CharField(max_length=100, blank=True)
    source = models.FileField(upload_to=random_temporary_dir, null=True, default=None)
    datetime = models.DateTimeField(auto_now_add=True)
    status = models.PositiveIntegerField(choices=STATUS_CHOICES, default=PROCESSING)
    stdout = models.TextField(default="")
    stderr = models.TextField(default="")

    def save(self, download_type=None, *args, **kwargs):
        pk = self.pk

        super().save(*args, **kwargs)

        if pk is not None:
            return

        if download_type is not None:
            chain(
                prepare_sources.si(self.id, download_type),
                perform_submission.si(self.id),
            )()

    def run(self):
        container_name = f'{self.id}_{self.assignment.environment.tag}'
        student_attachments_dir = os.path.join(settings.HOST_MEDIA_ROOT, self.store_dir)
        teacher_attachments_dir = os.path.join(settings.HOST_MEDIA_ROOT, self.assignment.course.attachments_path)

        with docker.DockerContainer(self.assignment.environment.tag, container_name) as container:
            container.run('-i', '-d',
                          f'--volume={student_attachments_dir}:/student-attachments:ro',
                          f'--volume={teacher_attachments_dir}:/teacher-attachments:ro',
                          command='bash')
            container.exec(command='bash', command_args=['-c', "'cp /student-attachments/* /src'"])
            container.exec(command='bash', command_args=['-c', "'cp /teacher-attachments/* /src'"])

            self.status = Submission.PERFORMED
            for rule in self.assignment.rules.order_by('order'):
                timeout = f"timeout {rule.timeout}" if rule.timeout else ''
                ret_code = container.exec(command='bash', command_args=['-c', f"'{timeout} {rule.command}'"])
                if ret_code != 0 and not rule.continue_on_fail:
                    self.status = Submission.FAILED
                    break

        self.stdout = container.output
        self.save()

    @property
    def store_dir(self):
        """Location within MEDIA_ROOT directory where submission should be stored."""
        course_id = self.assignment.course.id
        return f"courses/course_{course_id}/submissions/submission_{self.id}"

    def __str__(self):
        return f"Submission <id={self.id}, user='{self.user}', assignment='{self.assignment}'>"
