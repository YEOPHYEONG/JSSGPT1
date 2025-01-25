from django.test import TestCase
from .models import UserCoverLetter
from django.contrib.auth.models import User
from langchain_app.models import RecruitJob, CoverLetterPrompt

class UserCoverLetterTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.recruit_job = RecruitJob.objects.create(title="Software Engineer")
        self.prompt = CoverLetterPrompt.objects.create(question_text="Why do you want this job?")

    def test_create_cover_letter(self):
        cover_letter = UserCoverLetter.objects.create(
            user=self.user,
            recruit_job=self.recruit_job,
            prompt=self.prompt,
            content="This is a test cover letter.",
            draft=True
        )
        self.assertEqual(cover_letter.content, "This is a test cover letter.")