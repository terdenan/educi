from django.test import TestCase

from courses.models import Course, Environment
from build_rules.models import Rule

from courses.tests.test_models import SAMPLE_ENVIRONMENT


class TestRuleModel(TestCase):

    def setUp(self):
        self.course = Course.objects.create(title="Test course", description="Test course description")
        self.environment = Environment.objects.create(course=self.course, **SAMPLE_ENVIRONMENT)
        self.assignment = self.course.add_assignment(title="Test assignment", environment=self.environment,
                                                     description="Test assignment description")

    def test_can_create_a_rule(self):
        rule = Rule.objects.create(title="Test rule", order=0,command="echo Hello, world!",
                                   assignment=self.assignment)
        self.assertEqual(Rule.objects.first(), rule)

    def test_string_representation(self):
        rule = Rule(title="Test rule", order=0, command="echo Hello, world!")
        self.assertEqual("Test rule", str(rule))
