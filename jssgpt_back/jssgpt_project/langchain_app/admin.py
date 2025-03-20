from django import forms
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
import datetime
from .models import Company, Recruitment, RecruitJob, CoverLetterPrompt
from .tasks import crawl_recruitments_task  # 수정된 Celery 태스크

# 크롤링 폼 정의 (기업명 필드 추가 + 크롤링 기준 선택 추가)
class CrawlForm(forms.Form):
    date = forms.DateField(label="크롤링할 날짜", widget=forms.SelectDateWidget)
    company_name = forms.CharField(label="기업명 (선택, 여러 개는 쉼표로 구분)", required=False)
    crawl_mode = forms.ChoiceField(
        label="크롤링 기준",
        choices=[("start", "시작 날짜 기준"), ("end", "종료 날짜 기준")],
        initial="start"
    )

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
                date = form.cleaned_data["date"]
                target_date_str = date.strftime("%Y%m%d")
                company_names_str = form.cleaned_data.get("company_name")
                crawl_mode = form.cleaned_data.get("crawl_mode", "start")
                if company_names_str:
                    company_names = [name.strip() for name in company_names_str.split(",") if name.strip()]
                else:
                    company_names = None
                crawl_recruitments_task.delay(target_date_str, company_names, crawl_mode)
                self.message_user(
                    request, 
                    f"{target_date_str}의 크롤링 작업이 큐에 등록되었습니다. (기업: {company_names_str or '전체'}, 기준: {crawl_mode})", 
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

admin.site.register(Company)
admin.site.register(RecruitJob)
admin.site.register(Recruitment, RecruitmentAdmin)
admin.site.register(CoverLetterPrompt)
