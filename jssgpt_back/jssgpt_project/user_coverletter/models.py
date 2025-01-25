from django.db import models
from django.contrib.auth.models import User
from langchain_app.models import RecruitJob, CoverLetterPrompt
from user_experience.models import STARExperience

class UserCoverLetter(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cover_letters")
    recruit_job = models.ForeignKey(RecruitJob, on_delete=models.CASCADE, related_name="cover_letters")
    prompt = models.ForeignKey(CoverLetterPrompt, on_delete=models.CASCADE, related_name="user_prompts")
    recommended_starexperience = models.ManyToManyField(STARExperience, blank=True, related_name="recommended_cover_letters")
    selected_starexperience = models.ForeignKey(STARExperience, on_delete=models.SET_NULL, blank=True, null=True, related_name="selected_cover_letters")
    content = models.TextField(blank=True, null=True, default="")
    draft = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "recruit_job", "prompt")

    def __str__(self):
        return f"{self.user.username} - {self.recruit_job.title} - {self.prompt.question_text}"