from django.contrib import admin
from .models import UserCoverLetter

@admin.register(UserCoverLetter)
class UserCoverLetterAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recruit_job', 'prompt', 'selected_starexperience', 'draft', 'created_at', 'updated_at')
    list_filter = ('user', 'recruit_job', 'draft')
    search_fields = ('content', 'prompt__question_text', 'selected_starexperience__title')