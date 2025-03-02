# langchain_app/management/commands/crawl_todays_recruitments.py
import asyncio
import datetime
from django.core.management.base import BaseCommand
from langchain_app.crawler import integrated_crawler
from langchain_app.models import Recruitment, Company

class Command(BaseCommand):
    help = '오늘 날짜의 채용 공고를 크롤링하여 DB에 저장합니다.'

    def handle(self, *args, **options):
        today_str = datetime.datetime.today().strftime("%Y%m%d")
        self.stdout.write(f"[INFO] 오늘 날짜({today_str}) 크롤링 시작")
        
        companies_data = asyncio.run(integrated_crawler(today_str))
        
        if not companies_data:
            self.stdout.write("[INFO] 크롤링 결과가 없습니다.")
            return
        
        for comp in companies_data:
            # start_date는 크롤러에서 YYYYMMDD 문자열로 수집되었음을 가정
            try:
                start_date = datetime.datetime.strptime(comp.get("start_date"), "%Y%m%d").date()
            except Exception:
                start_date = datetime.date.today()
            try:
                end_date_str = comp.get("end_date")
                end_date = datetime.datetime.strptime(end_date_str, "%Y.%m.%d").date() if end_date_str else start_date
            except Exception:
                end_date = start_date

            company_name = comp.get("company_name")
            recruitment_link = comp.get("link")

            company, _ = Company.objects.get_or_create(name=company_name)
            recruitment = Recruitment.objects.create(
                company=company,
                title=f"{company_name} 채용 공고",
                start_date=start_date,
                end_date=end_date,
                recruitment_link=recruitment_link,
            )
            self.stdout.write(f"[INFO] 저장 완료: {recruitment}")
        
        self.stdout.write("[INFO] 크롤링 및 DB 저장 작업 완료")
