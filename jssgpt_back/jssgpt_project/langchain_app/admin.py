# langchain_app/admin.py
from django import forms
from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
import asyncio
import datetime
from .models import Company, Recruitment, RecruitJob, CoverLetterPrompt
from .crawler import integrated_crawler

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
                companies_data = asyncio.run(integrated_crawler(target_date_str))
                
                if companies_data:
                    for comp in companies_data:
                        try:
                            start_date = datetime.datetime.strptime(comp.get("start_date"), "%Y%m%d").date()
                        except Exception:
                            start_date = date
                        try:
                            end_date_str = comp.get("end_date")
                            end_date = datetime.datetime.strptime(end_date_str.split(" ")[0], "%Y년 %m월 %d일").date() if end_date_str else start_date
                        except Exception:
                            end_date = start_date

                        company_name = comp.get("company_name")
                        recruitment_link = comp.get("recruitment_link")
                        jss_link = comp.get("link")
                        if not company_name:
                            continue
                        company, _ = Company.objects.get_or_create(name=company_name)
                        recruitment = Recruitment.objects.create(
                            company=company,
                            title=f"{company_name} 채용 공고",
                            start_date=start_date,
                            end_date=end_date,
                            recruitment_link=recruitment_link,
                            jss_link=jss_link
                        )
                        employment_id = comp.get("employment_id")
                        if employment_id:
                            recruitment, created = Recruitment.objects.update_or_create(
                            custom_id=employment_id,
                            defaults={
                                'company': company,
                                'title': f"{company_name} 채용 공고",
                                'start_date': start_date,
                                'end_date': end_date,
                                'recruitment_link': recruitment_link,
                                'jss_link': jss_link,
                            }
                        )
                        else:
                            recruitment = Recruitment.objects.create(
                                company=company,
                                title=f"{company_name} 채용 공고",
                                start_date=start_date,
                                end_date=end_date,
                                recruitment_link=recruitment_link,
                                jss_link=jss_link
                            )

                        jobs_data = comp.get("jobs", [])
                        for job_data in jobs_data:
                            recruit_job = RecruitJob.objects.create(
                                recruitment=recruitment,
                                title=job_data.get("recruitment_title"),
                                recruitment_type=job_data.get("recruitment_type")
                            )
                            essay_questions = job_data.get("essay_questions", [])
                            for essay in essay_questions:
                                question_text = essay.get("question")
                                limit_str = essay.get("limit")
                                limit = None
                                if limit_str:
                                    try:
                                        limit = int(limit_str.replace("(", "").replace(")", "").replace("자", "").strip())
                                    except Exception as e:
                                        print(f"[ERROR] limit 파싱 실패: {e}")
                                        limit = None
                                # 단순히 CoverLetterPrompt 객체를 생성합니다.
                                CoverLetterPrompt.objects.create(
                                    recruit_job=recruit_job,
                                    question_text=question_text,
                                    limit=limit
                                )
                    self.message_user(request, f"{target_date_str}의 크롤링 작업이 완료되었습니다.")
                else:
                    self.message_user(request, "크롤링 결과가 없습니다.")
                return redirect("..")
        else:
            form = CrawlForm()
        context = dict(self.admin_site.each_context(request), form=form)
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
