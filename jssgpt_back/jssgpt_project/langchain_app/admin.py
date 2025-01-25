from django.contrib import admin
from .models import Company, Recruitment, RecruitJob, CoverLetterPrompt

class CoverLetterPromptInline(admin.TabularInline):
    model = CoverLetterPrompt
    extra = 0

class RecruitJobAdmin(admin.ModelAdmin):
    list_display = ("id", "recruitment", "title", "description", "required_skills", "soft_skills", "key_strengths")
    inlines = [CoverLetterPromptInline]  # 자기소개서 문항을 인라인으로 표시

class RecruitmentAdmin(admin.ModelAdmin):
    list_display = ("company", "title", "start_date", "end_date")

from django.contrib import admin
from langchain_app.models import CoverLetterPrompt

@admin.register(CoverLetterPrompt)
class CoverLetterPromptAdmin(admin.ModelAdmin):
    list_display = ('id', 'recruit_job', 'question_text', 'created_at')

admin.site.register(Company)
admin.site.register(RecruitJob, RecruitJobAdmin)
admin.site.register(Recruitment, RecruitmentAdmin)
