from django.test import TestCase
from django.contrib.auth import get_user_model

from courses.models import Course, Environment
from submissions.models import Submission

from courses.tests.test_models import SAMPLE_ENVIRONMENT

User = get_user_model()


class TestSubmissionModel(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('test@mail.com')
        self.course = Course.objects.create(title="Test course", description="Test course description")
        self.environment = Environment.objects.create(course=self.course, **SAMPLE_ENVIRONMENT)
        self.assignment = self.course.add_assignment(title='Test assignment', environment=self.environment,
                                                     description='Test assignment description')
        self.submission = Submission.objects.create(assignment=self.assignment, user=self.user,
                                                    repo_url='testurl.com', branch='test')

    def test_string_representation(self):
        self.assertEqual(str(self.submission),
                         f"Submission <id={self.submission.id}, user='{self.user}', assignment='{self.assignment}'>")

    def test_can_create_submissions(self):
        inserted_submission = Submission.objects.first()

        self.assertEqual(inserted_submission, self.submission)
