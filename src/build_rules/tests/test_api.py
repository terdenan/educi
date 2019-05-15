import json

from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase
from rest_framework import status

from rest_framework_simplejwt.tokens import AccessToken

from build_rules.models import Rule
from courses.models import Course, Assignment, Membership, Environment

User = get_user_model()


class RuleAPITestCase(APITestCase):

    def setUp(self):
        self.teacher = User.objects.create(email="teacher@example.com")
        self.ta = User.objects.create(email="ta@example.com")
        self.student = User.objects.create(email="student@example.com")

        self.course = Course.objects.create(
            title="Test course",
            description="Test course description"
        )
        self.course.add_member(self.teacher, Membership.TEACHER)
        self.course.add_member(self.ta, Membership.TA)
        self.course.add_member(self.student, Membership.STUDENT)

        self.environment = Environment.objects.create(
            course=self.course,
            title="Test environment",
            dockerfile_content="FROM python:3.7\nRUN mkdir /src\nWORKDIR /src\n",
            tag="test_env"
        )

        self.assignment = self.course.add_assignment(
            environment=self.environment,
            title="Test assignment",
            description="Test assignment's description"
        )

        self.teacher_access_token = AccessToken.for_user(self.teacher)
        self.ta_access_token = AccessToken.for_user(self.ta)
        self.student_access_token = AccessToken.for_user(self.student)


class RuleListCreateAPIViewTest(RuleAPITestCase):

    def setUp(self):
        super().setUp()

        for order in range(5):
            Rule.objects.create(
                assignment=self.assignment,
                order=order,
                title='Test',
                description='Test description',
                command='Test_Command',
                timeout=1,
                continue_on_fail=True,
            )

        self.list_create_url = reverse(
            'courses:build_rules:list',
            kwargs={
                'pk': self.course.id,
                'assignment_id': self.assignment.id
            }
        )

    def test_teacher_can_create_a_rule(self):
        payload = {
            'order': 5,
            'title': 'Test',
            'description': 'Test description',
            'command': 'Test_Command',
            'timeout': 1,
            'continue_on_fail': True,
        }

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        response = self.client.post(self.list_create_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.assignment.rules.count(), 6)

    def test_ta_cant_create_a_rule(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.post(self.list_create_url, payload={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cant_create_a_rule(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.post(self.list_create_url, payload={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_get_a_list_of_rules(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_ta_can_get_a_list_of_rules(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_student_cant_get_a_list_of_rules(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RuleRetrieveUpdateDestroyAPIViewTest(RuleAPITestCase):

    def setUp(self):
        super().setUp()

        self.rule = Rule.objects.create(
            assignment=self.assignment,
            order=1,
            title='Test',
            description='Test description',
            command='Test_Command',
            timeout=1,
            continue_on_fail=True,
        )

        self.detail_url = reverse(
            'courses:build_rules:detail',
            kwargs={
                'pk': self.course.id,
                'assignment_id': self.assignment.id,
                'rule_id': self.rule.id
            }
        )

    def test_teacher_can_get_a_rule(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ta_can_get_a_rule(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_student_cant_get_a_rule(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_delete_a_rule(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Rule.objects.count(), 0)

    def test_ta_cant_delete_a_rule(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Rule.objects.count(), 1)

    def test_student_cant_delete_a_rule(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Rule.objects.count(), 1)

    def test_teacher_can_update_a_rule(self):
        payload = {
            'title': 'Test rule updated',
            'order': 2,
            'command': 'Test_Command_Updated',
        }

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        response = self.client.put(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        rule = Rule.objects.get(id=self.rule.id)
        self.assertEqual(rule.title, payload['title'])
        self.assertEqual(rule.order, payload['order'])
        self.assertEqual(rule.command, payload['command'])

    def test_ta_cant_update_a_rule(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.put(self.detail_url, payload={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cant_update_a_rule(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.put(self.detail_url, payload={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_partially_update_a_rule(self):
        payload = {
            'order': 3,
            'command': 'Test_Command_Partially_Updated',
        }

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        response = self.client.patch(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        rule = Rule.objects.get(id=self.rule.id)
        self.assertEqual(rule.order, payload['order'])
        self.assertEqual(rule.command, payload['command'])

    def test_ta_cant_partially_update_a_rule(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.patch(self.detail_url, payload={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cant_partially_update_a_rule(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.patch(self.detail_url, payload={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
