from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from courses.models import CourseCreationRequest as CCR
from courses.models import Course
User = get_user_model()


class TestCourseAdmin(TestCase):

    def setUp(self):
        admin_user = User.objects.create_superuser(
            email="admin@test.com",
            password="secret"
        )
        self.client.force_login(admin_user)
        self.user = User.objects.create(email="user@mail.com")

        self.ccr1 = CCR.objects.create(user=self.user, title="Course #1", description="Description")
        self.ccr2 = CCR.objects.create(user=self.user, title="Course #2", description="Description")
        self.ccr3 = CCR.objects.create(user=self.user, title="Course #3", description="Description")

    def test_can_approve_requests(self):
        change_url = reverse('admin:courses_coursecreationrequest_changelist')
        data = {
            'action': 'approve_requests',
            '_selected_action': [self.ccr1.pk, self.ccr3.pk]
        }
        response = self.client.post(change_url, data)

        self.assertEqual(CCR.objects.filter(status=CCR.APPROVED).count(), 2)
        self.assertEqual(CCR.objects.filter(status=CCR.CONSIDERING).count(), 1)
        self.assertEqual(Course.objects.count(), 2)

    def test_can_approve_requests(self):
        change_url = reverse('admin:courses_coursecreationrequest_changelist')
        data = {
            'action': 'refuse_requests',
            '_selected_action': [self.ccr1.pk, self.ccr3.pk]
        }
        response = self.client.post(change_url, data)

        self.assertEqual(CCR.objects.filter(status=CCR.REFUSED).count(), 2)
        self.assertEqual(CCR.objects.filter(status=CCR.CONSIDERING).count(), 1)
        self.assertEqual(Course.objects.count(), 0)
