from django.test import TestCase
from django.urls import reverse

class GoogleLoginCallbackTestCase(TestCase):
    def test_google_callback(self):
        response = self.client.post(reverse('google_callback'), data={
            'access_token': 'fake-token'
        })
        self.assertEqual(response.status_code, 401)  # 인증 실패 테스트
