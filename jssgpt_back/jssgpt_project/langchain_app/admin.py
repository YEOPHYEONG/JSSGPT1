from django import forms
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
import datetime
from .models import Company, Recruitment, RecruitJob, CoverLetterPrompt
from .tasks import crawl_recruitments_task  # 새로 만든 Celery 태스크

# 크롤링 폼 정의
class CrawlForm(forms.Form):
    date = forms.DateField(label="크롤링할 날짜", widget=forms.SelectDateWidget)

# RecruitmentAdmin에 커스텀 URL을 추가하여 크롤링 뷰를 제공
class RecruitmentAdmin(admin.ModelAdmin):
    list_display = ("company", "title", "start_date", "end_date")
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('crawl_recruitments/', self.admin_site.admin_view(self.crawl_view), name="crawl_recruitments"),
        ]
        return custom_urls + urls

    def crawl_view(self, request):
        if request.method == "POST":
            form = CrawlForm(request.POST)
            if form.is_valid():
                # 선택한 날짜를 YYYYMMDD 문자열로 변환
                date = form.cleaned_data["date"]
                target_date_str = date.strftime("%Y%m%d")
                
                # Celery 태스크를 큐에 등록하여 백그라운드에서 크롤링 실행
                crawl_recruitments_task.delay(target_date_str)
                
                # 관리자에게 작업이 큐에 등록되었음을 알림
                self.message_user(
                    request, 
                    f"{target_date_str}의 크롤링 작업이 큐에 등록되었습니다.", 
                    level=messages.INFO
                )
                return redirect("..")
        else:
            form = CrawlForm()
        context = dict(
            self.admin_site.each_context(request),
            form=form,
            subtitle="크롤링 실행",
            title="특정 날짜 크롤링"
        )
        return render(request, "admin/crawl_form.html", context)

# 인라인으로 CoverLetterPrompt를 표시
class CoverLetterPromptInline(admin.TabularInline):
    model = CoverLetterPrompt
    extra = 0

class RecruitJobAdmin(admin.ModelAdmin):
    list_display = ("id", "recruitment", "title", "description", "required_skills", "soft_skills", "key_strengths")
    inlines = [CoverLetterPromptInline]

@admin.register(CoverLetterPrompt)
class CoverLetterPromptAdmin(admin.ModelAdmin):
    list_display = ('id', 'recruit_job', 'question_text', 'created_at')

admin.site.register(Company)
admin.site.register(RecruitJob, RecruitJobAdmin)
admin.site.register(Recruitment, RecruitmentAdmin)
