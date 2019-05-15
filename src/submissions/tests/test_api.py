from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from rest_framework_simplejwt.tokens import AccessToken

from courses.models import Course, Membership, Environment, Assignment
from build_rules.models import Rule
from submissions.models import Submission

from courses.tests.test_models import SAMPLE_ENVIRONMENT

User = get_user_model()


class SubmissionAPIViewTest(APITestCase):

    def setUp(self):
        self.teacher = User.objects.create(email="teacher@mail.com")
        self.ta = User.objects.create(email="ta@mail.com")
        self.student = User.objects.create(email="student@mail.com")

        self.course = Course.objects.create(
            title="Test course",
            description="Test description",
        )
        self.course.add_member(self.teacher, Membership.TEACHER)
        self.course.add_member(self.ta, Membership.TA)
        self.course.add_member(self.student, Membership.STUDENT)

        self.teacher_access_token = AccessToken.for_user(self.teacher)
        self.ta_access_token = AccessToken.for_user(self.ta)
        self.student_access_token = AccessToken.for_user(self.student)

        self.environment = Environment.objects.create(
            course=self.course,
            title="Test environment",
            dockerfile_content="FROM python:3.7\nRUN mkdir /src\nWORKDIR /src\n",
            tag="test_image",
        )
        self.assignment = Assignment.objects.create(
            course=self.course,
            environment=self.environment,
            title="Test assignment",
            description="Test assignment description",
        )
        self.rule = Rule.objects.create(
            title="Test rule",
            description="Test rule description",
            order=1,
            command="python caesar.py",
            timeout=None,
            continue_on_fail=True,
            assignment=self.assignment,
        )
        self.submission = Submission(
            assignment=self.assignment,
            user=self.teacher,
            repo_url='github.com/terdenan/test-educi',
            branch='master'
        )
        self.submission.save(download_type=Submission.STRATEGY_REPOSITORY)

        self.submission_list_url = reverse('courses:submissions:list', args=(self.course.id,))
        self.submission_detail_url = reverse('courses:submissions:detail', args=(self.course.id, self.submission.id,))

    def test_can_get_list_of_submissions(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        response = self.client.get(self.submission_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], self.teacher.id)

    def test_can_get_submission(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        response = self.client.get(self.submission_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.teacher.id)

    def test_can_create_submission(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        test_submission = {'assignment': self.assignment.id,
                           'repo_url': 'github.com/terdenan/test-educi',
                           'branch': 'master',
                           'type': Submission.STRATEGY_REPOSITORY}
        response = self.client.post(self.submission_list_url, test_submission)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.teacher.id)
        self.assertEqual(response.data['status'], Submission.PROCESSING)

        response = self.client.get(reverse('courses:submissions:detail',
                                           args=(self.course.id, response.data['id'])))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Submission.PERFORMED)


class UserSubmissionsAPIViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user("test@mail.com")
        self.course = Course.objects.create(title="Test course", description="Test course description")
        self.environment = Environment.objects.create(course=self.course, **SAMPLE_ENVIRONMENT)
        self.course.add_member(self.user, Membership.TEACHER)
        self.assignment = self.course.add_assignment(title="Test assignment", environment=self.environment,
                                                     description="Test assignment description")
        self.submission = Submission.objects.create(assignment=self.assignment, user=self.user,
                                                    repo_url='github.com/terdenan/test-educi', branch='master')
        self.submission_list_url = reverse('courses:submissions:list',
                                           args=(self.course.id,))

    def test_can_list_user_submissions(self):
        user = User.objects.create_user("test2@mail.com")
        self.course.add_member(user, Membership.STUDENT)

        access_token = AccessToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(access_token))

        test_submission = {'assignment': self.assignment.id,
                           'repo_url': 'github.com/terdenan/test-educi',
                           'branch': 'master',
                           'type': Submission.STRATEGY_REPOSITORY,}

        response = self.client.post(self.submission_list_url, test_submission)
        self.assertEqual(response.data['user'], user.id)
        self.assertEqual(response.data['status'], Submission.PROCESSING)

        user_submissions_list_url = reverse("courses:submissions:user-list", args=(self.course.id, user.id))
        response = self.client.get(user_submissions_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], Submission.PERFORMED)
