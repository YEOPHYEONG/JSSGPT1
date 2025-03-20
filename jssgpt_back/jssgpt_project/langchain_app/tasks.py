import asyncio
import json
import logging
from celery import shared_task
from asgiref.sync import sync_to_async
from .models import Company, RecruitJob, CoverLetterPrompt
from .utils import (
    generate_and_save_company_info,
    generate_and_save_job_info,
    generate_and_save_cover_letter_outline,
)

logger = logging.getLogger(__name__)

@shared_task
def crawl_recruitments_task(target_date_str, company_name=None):
    from .crawler import main  # main()는 비동기 generator wrapper
    try:
        logger.info(f"Starting Celery task for target_date: {target_date_str}, company: {company_name}")
        async def process_crawl():
            async for company in main(target_date_str, company_name):
                try:
                    from .utils_crawler import save_company_data
                    # 크롤링된 각 기업 데이터를 바로 DB에 저장
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
        if company.industry in (None, ""):
            generate_and_save_company_info(company.name)
            logger.info(f"Company info task executed for Company id {company_id}.")
        else:
            logger.info("Company info already set for Company id %s, skipping.", company_id)
        return company.id
    except Company.DoesNotExist:
        logger.error(f"Company id {company_id} not found.")
        return "Company not found."

@shared_task
def generate_job_info_task(recruit_job_id):
    try:
        from .models import RecruitJob
        recruit_job = RecruitJob.objects.get(id=recruit_job_id)
        if recruit_job.description in (None, ""):
            generate_and_save_job_info(
                recruit_job.recruitment.company.name,
                recruit_job.recruitment,
                recruit_job.title,
                recruit_job
            )
            logger.info(f"Job info task executed for RecruitJob id {recruit_job_id}.")
        else:
            logger.info("Job info already set for RecruitJob id %s, skipping.", recruit_job_id)
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
