import json
from time import sleep

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.utils import IntegrityError
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken

from courses.models import Course, Membership, Assignment, Environment, CourseCreationRequest
from courses.tasks import delete_docker_image

User = get_user_model()


SAMPLE_COURSE = {
    "title": "Test course",
    "description": "Test course description"
}


class CourseAPIViewTest(APITestCase):

    def setUp(self):
        self.course = Course.objects.create(**SAMPLE_COURSE)

        self.user = User.objects.create(email="test@mail.com")
        self.superuser = User.objects.create_superuser(email="admin@mail.com", password="secret")

        self.course.add_member(self.user, Membership.TEACHER)

        self.user_access_token = AccessToken.for_user(self.user)
        self.superuser_access_token = AccessToken.for_user(self.superuser)

        self.course_detail_url = reverse('courses:detail', args=(self.course.id,))

    def test_get_course_list(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.user_access_token))

        response = self.client.get(reverse('courses:list'))
        response_course = json.loads(response.content)[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_course['title'], SAMPLE_COURSE['title'])
        self.assertEqual(Course.objects.count(), 1)

    def test_can_create_a_course(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.superuser_access_token))

        test_course = {
            "title": "Test course",
            "description": "Test course description"
        }
        response = self.client.post(reverse('courses:list'), test_course)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json.loads(response.content)['title'], test_course['title'])
        self.assertEqual(Course.objects.count(), 2)

    def test_can_get_existing_course(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.user_access_token))

        response = self.client.get(self.course_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], SAMPLE_COURSE['title'])

    def test_can_not_get_fake_course(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.user_access_token))

        response = self.client.get(reverse('courses:detail', args=(100,)))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_can_update_a_course(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.user_access_token))

        updated_course = {
            "title": "Updated test course",
            "description": "Test course description"
        }
        response = self.client.put(self.course_detail_url, updated_course)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Course.objects.get(pk=self.course.id).title, updated_course['title'])

    def test_can_delete_a_course(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.superuser_access_token))

        response = self.client.delete(self.course_detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Course.objects.count(), 0)


class CourseCreationRequestAPIViewTest(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create(email="test1@mail.com")
        self.user2 = User.objects.create(email="test2@mail.com")

        self.course_creation_request1 = CourseCreationRequest.objects.create(user=self.user1, title="Test title",
                                                                             description="Test description")
        self.course_creation_request2 = CourseCreationRequest.objects.create(user=self.user2, title="Test title",
                                                                             description="Test description")

        self.user1_access_token = AccessToken.for_user(self.user1)
        self.user2_access_token = AccessToken.for_user(self.user2)

        self.course_creation_request_list_url = reverse('courses:request-list')

    def test_can_get_own_requests(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user1_access_token}")
        response = self.client.get(self.course_creation_request_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], CourseCreationRequest.CONSIDERING)

    def test_can_post_request(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user1_access_token}")
        course_creation_request = {
            "title": "Test title",
            "description": "Test description"
        }
        response = self.client.post(self.course_creation_request_list_url, course_creation_request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(self.course_creation_request_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class CourseMembersAPIViewTest(APITestCase):

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

        self.course_members_list_url = reverse('courses:members-list', args=(self.course.id,))
        self.course_members_detail_url = reverse('courses:members-detail', args=(self.course.id, self.student.id))

    def test_teacher_can_get_a_list_of_course_members(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        response = self.client.get(self.course_members_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_ta_can_get_a_list_of_course_members(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.get(self.course_members_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_student_cant_get_a_list_of_course_members(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.get(self.course_members_list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_add_a_user(self):
        user = User.objects.create(email="test@mail.com")
        payload = {
            'email': 'test@mail.com',
            'role': Membership.STUDENT,
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        response = self.client.post(self.course_members_list_url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user_id'], user.id)
        self.assertEqual(self.course.members.count(), 4)

    def test_ta_can_add_a_user(self):
        user = User.objects.create(email="test@mail.com")
        payload = {
            'email': 'test@mail.com',
            'role': Membership.STUDENT,
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.post(self.course_members_list_url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user_id'], user.id)
        self.assertEqual(self.course.members.count(), 4)

    def test_student_cant_add_a_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.post(self.course_members_list_url, {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_get_a_course_member(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        response = self.client.get(self.course_members_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.student.email)
        self.assertEqual(response.data['role'], Membership.STUDENT)

    def test_ta_can_get_a_course_member(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.get(self.course_members_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.student.email)
        self.assertEqual(response.data['role'], Membership.STUDENT)

    def test_student_can_get_himself_as_a_course_member(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.get(self.course_members_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.student.email)
        self.assertEqual(response.data['role'], Membership.STUDENT)

    def test_student_cant_get_another_course_member(self):
        user = User.objects.create(email="test@mail.com")
        self.course.add_member(user, Membership.STUDENT)
        request_url = reverse("courses:members-detail", args=(self.course.id, user.id))

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.get(request_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_not_add_fake_user_to_course(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        payload = {
            "email": "test2@mail.com",
            "role": Membership.STUDENT
        }
        response = self.client.post(self.course_members_list_url, payload)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_can_not_add_same_user_twice(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        payload = {
            "email": self.student.email,
            "role": Membership.STUDENT,
        }

        try:
            with transaction.atomic():
                response = self.client.post(self.course_members_list_url, payload)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            pass

        self.assertEqual(self.course.members.count(), 3)

    def test_teacher_can_remove_a_course_member(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        response = self.client.delete(self.course_members_detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.course.members.count(), 2)

    def test_ta_can_remove_a_course_member(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.delete(self.course_members_detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.course.members.count(), 2)

    def test_student_can_remove_himself_as_a_course_member(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.delete(self.course_members_detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.course.members.count(), 2)

    def test_student_cant_remove_another_course_member(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")

        user = User.objects.create(email="test@mail.com")
        self.course.add_member(user, Membership.STUDENT)
        request_url = reverse("courses:members-detail", args=(self.course.id, user.id))

        response = self.client.delete(request_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.course.members.count(), 4)


class AssignmentAPIViewTest(APITestCase):

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

        self.assignments_list_url = reverse('courses:assignments-list', args=(self.course.id,))
        self.assignments_detail_url = reverse('courses:assignments-detail', args=(self.course.id, self.assignment.id))

    def test_teacher_can_create_an_assignment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")

        payload = {
            'environment': self.environment.id,
            'title': "Test assignment 2",
            'description': "Test assignment 2 description",
        }
        response = self.client.post(self.assignments_list_url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.course.assignments.count(), 2)
        self.assertEqual(response.data['title'], payload['title'])

    def test_ta_cant_create_an_assignment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.post(self.assignments_list_url, {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cant_create_an_assignment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.post(self.assignments_list_url, {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_create_assignment_with_invalid_data(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        payload = {
            "title": "Invalid assignment"
        }
        response = self.client.post(self.assignments_list_url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Assignment.objects.count(), 1)

    # def test_cant_create_assignment_related_to_a_fake_course(self):
    #     self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
    #
    #     fake_url = reverse('courses:assignments-list', args=(100,))
    #     response = self.client.post(fake_url, {})
    #
    #     self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    #     self.assertEqual(Assignment.objects.count(), 1)

    def test_teacher_can_update_assignment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")

        payload = {
            'environment': self.environment.id,
            'title': "Updated test assignment",
            'description': "Updated test assignment description",
        }
        response = self.client.put(self.assignments_detail_url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        assignment = Assignment.objects.get(pk=self.assignment.id)
        self.assertEqual(assignment.environment.id, payload['environment'])
        self.assertEqual(assignment.title, payload['title'])
        self.assertEqual(assignment.description, payload['description'])

    def test_ta_cant_update_assignment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.put(self.assignments_detail_url, {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cant_update_assignment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.put(self.assignments_detail_url, {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_partially_update_assignment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")

        payload = {
            'description': "Updated test assignment description",
        }
        response = self.client.patch(self.assignments_detail_url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        assignment = Assignment.objects.get(pk=self.assignment.id)
        self.assertEqual(assignment.description, payload['description'])

    def test_ta_cant_partially_update_assignment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.put(self.assignments_detail_url, {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cant_partially_update_assignment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.put(self.assignments_detail_url, {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_delete_an_assignment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        response = self.client.delete(self.assignments_detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.course.assignments.count(), 0)

    def test_ta_cant_delete_an_assignment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.delete(self.assignments_detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.course.assignments.count(), 1)

    def test_student_cant_delete_an_assignment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.delete(self.assignments_detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.course.assignments.count(), 1)

    # def test_can_not_delete_fake_assignment(self):
    #     response = self.client.delete(reverse('courses:assignments-detail', args=(self.course.id, 100)))
    #
    #     self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_teacher_can_get_list_of_assignments(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        response = self.client.get(self.assignments_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_ta_can_get_list_of_assignments(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.get(self.assignments_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_student_can_get_list_of_assignments(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.get(self.assignments_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class EnvironmentAPIViewTest(APITestCase):

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

        self.environment_list_url = reverse('courses:environment-list', args=(self.course.id,))
        self.environment_detail_url = reverse('courses:environment-detail', args=(self.course.id, self.environment.id))

    def test_teacher_can_create_an_environment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        payload = {
            'course': self.course.id,
            'title': "Test environment",
            'dockerfile_content': "FROM python:3.7\nRUN mkdir /src\nWORKDIR /src\n",
            'tag': "test_image2",
        }
        response = self.client.post(self.environment_list_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], Environment.PROCESSING)
        self.assertEqual(Environment.objects.count(), 2)

        environment_id = response.data['id']
        environment_detail_url = reverse('courses:environment-detail', args=(self.course.id, environment_id))

        response = self.client.get(environment_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Environment.CREATED)

        delete_docker_image(payload['tag'])

    def test_ta_cant_create_an_environment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.post(self.environment_list_url, {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Environment.objects.count(), 1)

    def test_student_cant_create_an_environment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.post(self.environment_list_url, {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Environment.objects.count(), 1)

    def test_teacher_can_get_list_of_environments(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        response = self.client.get(self.environment_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_ta_can_get_list_of_environments(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.get(self.environment_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_student_cant_get_list_of_environments(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.get(self.environment_list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_get_an_environment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        response = self.client.get(self.environment_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.environment.id)
        self.assertEqual(response.data['status'], Environment.CREATED)

    def test_ta_can_get_an_environment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.get(self.environment_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.environment.id)
        self.assertEqual(response.data['status'], Environment.CREATED)

    def test_student_cant_get_an_environment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.get(self.environment_detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_delete_an_environment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")
        response = self.client.delete(self.environment_detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Environment.objects.count(), 0)

    def test_ta_cant_delete_an_environment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.delete(self.environment_detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Environment.objects.count(), 1)

    def test_student_cant_delete_an_environment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.delete(self.environment_detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Environment.objects.count(), 1)

    def test_teacher_can_update_an_environment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")

        payload = {
            'title': "Updated test environment",
            'dockerfile_content': "FROM python:3.7\nRUN mkdir /src\nWORKDIR /src-upd\n",
            'tag': "updated_test_image2",
        }
        response = self.client.put(self.environment_detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Environment.PROCESSING)

        environment_id = response.data['id']
        environment_detail_url = reverse('courses:environment-detail', args=(self.course.id, environment_id))

        response = self.client.get(environment_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Environment.CREATED)

        delete_docker_image(payload['tag'])

    def test_ta_cant_update_an_environment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.put(self.environment_detail_url, {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cant_update_an_environment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.put(self.environment_detail_url, {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_partially_update_an_environments_dockerfile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")

        payload = {
            'dockerfile_content': "FROM python:3.7\nRUN mkdir /src\nWORKDIR /src-part-upd\n",
        }
        response = self.client.patch(self.environment_detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Environment.PROCESSING)

        environment_id = response.data['id']
        environment_detail_url = reverse('courses:environment-detail', args=(self.course.id, environment_id))

        response = self.client.get(environment_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Environment.CREATED)

        delete_docker_image(self.environment.tag)

    def test_teacher_can_partially_update_an_environments_title(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_access_token}")

        payload = {
            'title': "Updated test environment"
        }
        response = self.client.patch(self.environment_detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Environment.CREATED)

    def test_ta_cant_partially_update_an_environment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ta_access_token}")
        response = self.client.patch(self.environment_detail_url, {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cant_partially_update_an_environment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_access_token}")
        response = self.client.patch(self.environment_detail_url, {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
