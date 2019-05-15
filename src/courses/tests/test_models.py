from time import sleep

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from courses.models import Course, Assignment, Membership, Environment
from courses.tasks import delete_docker_image
from build_rules.models import Rule

User = get_user_model()


SAMPLE_ENVIRONMENT = {
    'title': "Test environment",
    'dockerfile_content': "FROM python:3.7\nRUN mkdir /src\nWORKDIR /src\n",
    'tag': "test_image",
}


class TestCourseModel(TestCase):

    def setUp(self):
        self.course = Course.objects.create(title="Test course", description="Test course description")
        self.env = Environment.objects.create(course=self.course, **SAMPLE_ENVIRONMENT)
        self.assignment = Assignment.objects.create(course=self.course, title="Test assignment",
                                                    description="Description", environment=self.env)

    def test_string_representation(self):
        self.assertEqual(str(self.course), "Test course")

    def test_can_create_a_course(self):
        course = Course.objects.create(title="Test course 2", description="Test course 2 description")

        self.assertEqual(len(Course.objects.all()), 2)
        self.assertEqual(Course.objects.get(pk=course.pk), course)

    def test_can_fill_a_course_with_members(self):
        user1 = User.objects.create_user(email="test1@example.com")
        user2 = User.objects.create_user(email="test2@example.com")

        self.course.add_member(user1, Membership.TEACHER)
        self.course.add_member(user2, Membership.TA)

        self.assertEqual(self.course.members.count(), 2)

    def test_can_remove_member_from_course(self):
        user = User.objects.create_user(email="test@example.com")
        self.course.add_member(user, Membership.STUDENT)

        self.assertEqual(self.course.members.count(), 1)
        self.course.remove_member(user.id)
        self.assertEqual(self.course.members.count(), 0)

    def test_can_not_remove_fake_user(self):
        user = User.objects.create_user(email="test@example.com")
        fake_id = 2019
        self.course.add_member(user, Membership.STUDENT)

        self.assertEqual(self.course.members.count(), 1)
        self.assertRaises(ObjectDoesNotExist, self.course.remove_member, user_id=fake_id)
        self.assertEqual(self.course.members.count(), 1)

    def test_can_not_remove_existing_user(self):
        user1 = User.objects.create_user(email="test1@example.com")
        user2 = User.objects.create_user(email="test2@example.com")

        self.course.add_member(user1, Membership.STUDENT)

        self.assertEqual(self.course.members.count(), 1)
        self.assertRaises(ObjectDoesNotExist, self.course.remove_member, user_id=user2.id)
        self.assertEqual(self.course.members.count(), 1)

    def test_can_check_if_user_is_course_member(self):
        user1 = User.objects.create_user(email="tes1t@example.com")
        user2 = User.objects.create_user(email="tes2t@example.com")
        self.course.add_member(user1, Membership.STUDENT)

        self.assertEqual(self.course.members.count(), 1)

        user1_is_member = self.course.has_member(user1.id)
        user2_is_member = self.course.has_member(user2.id)

        self.assertTrue(user1_is_member)
        self.assertFalse(user2_is_member)

    def test_can_get_role(self):
        user1 = User.objects.create_user(email="tes1t@example.com")
        user2 = User.objects.create_user(email="tes2t@example.com")
        user3 = User.objects.create_user(email="tes3t@example.com")
        user4 = User.objects.create_user(email="tes4t@example.com")

        self.course.add_member(user1, Membership.TEACHER)
        self.course.add_member(user2, Membership.TA)
        self.course.add_member(user3, Membership.STUDENT)

        self.assertEqual(self.course.members.count(), 3)

        user1_role = self.course.get_role(user1)
        user2_role = self.course.get_role(user2)
        user3_role = self.course.get_role(user3)
        user4_role = self.course.get_role(user4)

        self.assertTrue(user1_role == Membership.TEACHER)
        self.assertTrue(user2_role == Membership.TA)
        self.assertTrue(user3_role == Membership.STUDENT)
        self.assertTrue(user4_role is None)

    def test_can_add_assignment(self):
        assignment = self.course.add_assignment(title="Test assignment", description="Description",
                                                environment=self.env)
        self.assertEqual(self.course.assignments.count(), 2)
        self.assertEqual(self.course.assignments.get(pk=assignment.pk), assignment)

    def test_can_remove_assignment(self):
        self.course.remove_assignment(self.assignment.id)
        self.assertEqual(self.course.assignments.count(), 0)

    def test_can_not_remove_fake_assignment(self):
        fake_id = 2019
        self.assertEqual(self.course.assignments.count(), 1)
        self.assertRaises(ObjectDoesNotExist, self.course.remove_assignment, assignment_id=fake_id)
        self.assertEqual(self.course.assignments.count(), 1)


class TestAssignmentModel(TestCase):

    def setUp(self):
        self.course = Course.objects.create(title="Test course", description="Test course description")
        self.environment = Environment.objects.create(course=self.course, **SAMPLE_ENVIRONMENT)

    def test_can_create_assignment(self):
        assignment = Assignment.objects.create(course=self.course, environment=self.environment,
                                               title="Test assignment", description="Test assignment description")

        self.assertEqual(self.course.assignments.first(), assignment)

    def test_string_representation(self):
        assignment = Assignment.objects.create(course=self.course, environment=self.environment,
                                               title="Test assignment", description="Test assignment description")

        self.assertEqual(str(assignment), "Test assignment")

    def test_can_add_rule(self):
        assignment = self.course.add_assignment(title="Test assignment", environment=self.environment,
                                                description="Test assignment description")
        assignment.add_rule(title="Test rule", description="Test rule description", order=1,
                            continue_on_fail=True, command="echo Test", timeout=None)

        self.assertEqual(Rule.objects.count(), 1)
        self.assertEqual(assignment.rules.count(), 1)
        self.assertEqual(Rule.objects.first().title, "Test rule")

    def test_can_remove_rule(self):
        assignment = self.course.add_assignment(title="Test assignment", environment=self.environment,
                                                description="Test assignment description")
        rule = assignment.add_rule(title="Test rule", description="Test rule description", order=1,
                                   continue_on_fail=True, command="echo Test", timeout=None)
        assignment.remove_rule(rule.id)

        self.assertEqual(Rule.objects.count(), 0)
        self.assertEqual(assignment.rules.count(), 0)


class TestEnvironmentModel(TestCase):

    def setUp(self):
        self.course = Course.objects.create(title="Test course", description="Test course description")
        self.environment = Environment.objects.create(course=self.course, **SAMPLE_ENVIRONMENT)

    def test_string_representation(self):
        self.assertEqual(str(self.environment), 'Processing \'Test environment\'')

        self.environment.status = 1
        self.environment.save()

        self.assertEqual(str(self.environment), 'test_image: Test environment')

    def test_changes_status_after_creation(self):
        test_environment = {**SAMPLE_ENVIRONMENT, 'tag': 'test_image2'}
        env = Environment.objects.create(course=self.course, **test_environment)
        self.assertEqual(env.status, Environment.PROCESSING)

        sleep(1)

        updated_env = Environment.objects.get(pk=env.id)
        self.assertEqual(updated_env.status, Environment.CREATED)
        delete_docker_image(test_environment['tag'])
