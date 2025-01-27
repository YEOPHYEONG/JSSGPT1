from django.test import TestCase
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

class GoogleLoginCallbackTestCase(TestCase):

    @patch('social_django.utils.load_strategy')  # load_strategy를 Mocking
    @patch('social_django.backends.google.GoogleOAuth2.do_auth')  # do_auth를 Mocking
    def test_google_callback_new_user(self, mock_do_auth, mock_load_strategy):
        # Mocking된 Google 사용자 데이터
        mock_user = User(username='testuser', email='testuser@example.com')
        mock_do_auth.return_value = mock_user

        # Google Access Token이 주어졌을 때
        response = self.client.post(reverse('google_callback'), data={
            'access_token': 'fake-token'
        })

        # 응답 코드 확인 (JWT가 성공적으로 반환되었는지)
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.json())
        self.assertIn('user', response.json())

        # 생성된 사용자 확인
        created_user = User.objects.get(email='testuser@example.com')
        self.assertEqual(created_user.username, 'testuser')
        self.assertEqual(created_user.email, 'testuser@example.com')

    @patch('social_django.backends.google.GoogleOAuth2.do_auth')  # do_auth를 Mocking
    def test_google_callback_existing_user(self, mock_do_auth):
        # 이미 존재하는 사용자 생성
        existing_user = User.objects.create(username='existinguser', email='existing@example.com')

        # Mocking된 사용자 반환
        mock_do_auth.return_value = existing_user

        # Google Access Token이 주어졌을 때
        response = self.client.post(reverse('google_callback'), data={
            'access_token': 'fake-token'
        })

        # 응답 코드 확인 (JWT가 성공적으로 반환되었는지)
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.json())
        self.assertIn('user', response.json())

        # 기존 사용자 확인
        user = User.objects.get(email='existing@example.com')
        self.assertEqual(user.username, 'existinguser')
        self.assertEqual(user.email, 'existing@example.com')
