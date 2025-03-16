import asyncio
import json
import logging
from celery import shared_task
from asgiref.sync import sync_to_async  # 추가된 임포트
from .models import Company, RecruitJob, CoverLetterPrompt
from .utils import (
    generate_and_save_company_info,
    generate_and_save_job_info,
    generate_and_save_cover_letter_outline,
)

logger = logging.getLogger(__name__)

@shared_task
def crawl_recruitments_task(target_date_str):
    from .crawler import integrated_crawler
    try:
        logger.info(f"Starting Celery task for target_date: {target_date_str}")
        async def process_crawl():
            companies = await integrated_crawler(target_date_str)
            for company in companies:
                try:
                    from .utils_crawler import save_company_data
                    # sync_to_async로 동기 함수를 비동기로 호출
                    await sync_to_async(save_company_data)(company)
                    logger.info(f"Saved data for {company.get('company_name')}")
                except Exception as e:
                    logger.error(f"Error saving company {company.get('company_name')}: {e}", exc_info=True)
        asyncio.run(process_crawl())
        logger.info(f"Crawling data saved for target date {target_date_str}.")
        return True
    except Exception as e:
        logger.error(f"Error in Celery task: {e}", exc_info=True)
        return None
    
@shared_task
def generate_company_info_task(company_id):
    try:
        from .models import Company
        company = Company.objects.get(id=company_id)
        # 수정: industry가 None 또는 빈 문자열일 경우에만 생성
        if company.industry in (None, ""):
            generate_and_save_company_info(company.name)
            logger.info(f"Company info task executed for Company id {company_id}.")
        else:
            logger.info("Company info already set (not empty or None) for Company id %s, skipping.", company_id)
        return company.id
    except Company.DoesNotExist:
        logger.error(f"Company id {company_id} not found.")
        return "Company not found."

@shared_task
def generate_job_info_task(recruit_job_id):
    try:
        from .models import RecruitJob
        recruit_job = RecruitJob.objects.get(id=recruit_job_id)
        # 수정: description이 None 또는 빈 문자열일 경우에만 생성
        if recruit_job.description in (None, ""):
            generate_and_save_job_info(
                recruit_job.recruitment.company.name,
                recruit_job.recruitment,
                recruit_job.title,
                recruit_job
            )
            logger.info(f"Job info task executed for RecruitJob id {recruit_job_id}.")
        else:
            logger.info("Job info already set (not empty or None) for RecruitJob id %s, skipping.", recruit_job_id)
        return recruit_job.id
    except RecruitJob.DoesNotExist:
        logger.error(f"RecruitJob id {recruit_job_id} not found.")
        return "RecruitJob not found."

@shared_task
def generate_outline_task_for_prompt(prompt_id):
    try:
        prompt_instance = CoverLetterPrompt.objects.get(id=prompt_id)
        generate_and_save_cover_letter_outline(prompt_instance)
        logger.info(f"Outline task executed for CoverLetterPrompt id: {prompt_id}")
        return prompt_id
    except CoverLetterPrompt.DoesNotExist:
        logger.error(f"CoverLetterPrompt id {prompt_id} not found.")
        return "CoverLetterPrompt not found."