from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class TestUserModel(TestCase):

    def test_can_create_user(self):
        user = User.objects.create_user(email="test@example.com")
        self.assertEquals(User.objects.first(), user)

    def test_can_create_superuser(self):
        superuser = User.objects.create_superuser(email="test@example.com", password="secret")
        self.assertEquals(User.objects.first(), superuser)
        self.assertTrue(superuser.is_superuser)

    def test_string_representation(self):
        user = User.objects.create_user(email="test@example.com")
        self.assertEqual("test@example.com", str(user))

