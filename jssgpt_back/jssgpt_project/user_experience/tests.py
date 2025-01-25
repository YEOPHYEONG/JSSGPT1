from django.test import TestCase
from .models import RawExperience, STARExperience
from django.contrib.auth.models import User

class ResumeUploadTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')

    def test_raw_experience_creation(self):
        raw = RawExperience.objects.create(user=self.user, extracted_text="Sample text")
        self.assertEqual(raw.user.username, 'testuser')
        self.assertEqual(raw.extracted_text, "Sample text")