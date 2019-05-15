from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


class UserAPIViewTest(APITestCase):

    def setUp(self):
        self.user_email_address = 'user@example.com'
        self.user_password = 'secret_word'
        self.user = User.objects.create_user(self.user_email_address, self.user_password)

        access_token = AccessToken.for_user(self.user)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(access_token))

    def test_can_retrieve_user(self):
        response = self.client.get(reverse('users:detail'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user_email_address)
        self.assertEqual(response.data['id'], self.user.id)


class RegistrationAPITest(APITestCase):

    def setUp(self):
        self.user_email_address = 'user@example.com'
        self.user_password = 'secret_word'
        self.user = User.objects.create_user(self.user_email_address, self.user_password)
        self.register_url = reverse('users:register')

    def test_register_user(self):
        user_data = {
            'email': 'test_user@example.com',
            'password': 'secret_word'
        }

        response = self.client.post(self.register_url, user_data, format='json')
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], user_data['email'])
        self.assertFalse('password' in response.data)

    def test_register_user_with_invalid_email_address(self):
        user_data = {
            'email': 'test_user',
            'password': 'secret_word'
        }

        response = self.client.post(self.register_url, user_data, format='json')
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_without_email_address(self):
        user_data = {
            'email': '',
            'password': 'secret_word'
        }

        response = self.client.post(self.register_url, user_data, format='json')
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_with_an_existing_email_address(self):
        user_data = {
            'email': self.user_email_address,
            'password': 'secret_word'
        }

        response = self.client.post(self.register_url, user_data, format='json')
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_with_invalid_password(self):
        user_data = {
            'email': 'test_user@example.com',
            'password': 'secret'
        }

        response = self.client.post(self.register_url, user_data, format='json')
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_without_password(self):
        user_data = {
            'email': 'test_user@example.com',
            'password': ''
        }

        response = self.client.post(self.register_url, user_data, format='json')
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class JWTAuthenticationAPITest(APITestCase):

    def setUp(self):
        self.user_email_address = 'user@example.com'
        self.user_password = 'secret_word'
        self.user = User.objects.create_user(self.user_email_address, self.user_password)
        self.token_obtain_url = reverse('token_obtain_pair')
        self.token_refresh_url = reverse('token_refresh')

    def test_token_obtain(self):
        user_data = {
            'email': self.user_email_address,
            'password': self.user_password
        }

        response = self.client.post(self.token_obtain_url, user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access' in response.data)
        self.assertTrue('refresh' in response.data)

    def test_token_obtain_with_invalid_credentials(self):
        user_data = {
            'email': 'test_user@example.com',
            'password': 'secret_word'
        }

        response = self.client.post(self.token_obtain_url, user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_refresh(self):
        user_data = {
            'email': self.user_email_address,
            'password': self.user_password
        }
        response = self.client.post(self.token_obtain_url, user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access' in response.data)
        self.assertTrue('refresh' in response.data)

        refresh = response.data['refresh']
        response = self.client.post(self.token_refresh_url, {'refresh': refresh})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access' in response.data)
