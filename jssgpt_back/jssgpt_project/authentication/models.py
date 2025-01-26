from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=255, choices=[('google', 'Google'), ('kakao', 'Kakao')])
    social_id = models.CharField(max_length=255, unique=True)
    profile_image = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.provider})"
