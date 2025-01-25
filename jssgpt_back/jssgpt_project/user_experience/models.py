from django.db import models
from django.contrib.auth.models import User

class RawExperience(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='raw_experience')
    resume_file = models.FileField(upload_to='resumes/', blank=True, null=True)
    extracted_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Raw Experience"

class STARExperience(models.Model):
    raw_experience = models.ForeignKey(RawExperience, on_delete=models.CASCADE, related_name='star_experiences')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='star_experiences')
    title = models.CharField(max_length=255)
    situation = models.TextField()
    task = models.TextField()
    action = models.TextField()
    result = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"STARExperience: {self.title} (User: {self.user.username})"