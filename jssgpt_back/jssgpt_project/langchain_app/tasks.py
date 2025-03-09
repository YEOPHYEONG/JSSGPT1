import os
import sys
import subprocess
import json
import logging
from celery import shared_task
from django.conf import settings
from .models import Company, RecruitJob, CoverLetterPrompt
from .utils import (
    generate_and_save_company_info,
    generate_and_save_job_info,
    generate_and_save_cover_letter_outline,
)

logger = logging.getLogger(__name__)

@shared_task
def crawl_recruitments_task(target_date_str):
    logger.info("Current working directory in tasks.py: %s", os.getcwd())
    
    from pathlib import Path
    base_dir = str(Path(__file__).resolve().parent.parent)
    crawler_script_path = os.path.join(base_dir, "crawler_script.py")
    
    logger.info("settings.BASE_DIR: %s", settings.BASE_DIR)
    logger.info("Calculated project root (base_dir): %s", base_dir)
    logger.info("crawler_script_path: %s", crawler_script_path)
    
    cwd = base_dir
    env = os.environ.copy()
    try:
        result = subprocess.run(
            [sys.executable, crawler_script_path, target_date_str],
            capture_output=True, text=True, check=True,
            cwd=cwd,
            env=env
        )
        logger.info("stdout: %s", result.stdout)
        logger.error("stderr: %s", result.stderr)
        companies_data = json.loads(result.stdout)
        if companies_data:
            from .utils_crawler import save_crawled_json_data
            save_crawled_json_data(companies_data)
            logger.info(f"Crawling data saved for target date {target_date_str}.")
        else:
            logger.warning(f"No data returned for target date {target_date_str}.")
        return companies_data
    except subprocess.CalledProcessError as e:
        logger.error(f"[ERROR] 크롤러 스크립트 실행 실패: {e}", exc_info=True)
        return None
    except Exception as ex:
        logger.error(f"[ERROR] 태스크 실행 중 예외 발생: {ex}", exc_info=True)
        return None

@shared_task
def generate_company_info_task(company_id):
    try:
        from .models import Company
        company = Company.objects.get(id=company_id)
        if company.industry not in (None, "", "N/A"):
            logger.info("Company info already set for Company id %s, skipping.", company_id)
            return company.id
        generate_and_save_company_info(company.name)
        logger.info(f"Company info task executed for Company id {company_id}.")
    except Company.DoesNotExist:
        logger.error(f"Company id {company_id} not found.")
        return "Company not found."

@shared_task
def generate_job_info_task(recruit_job_id):
    try:
        from .models import RecruitJob
        recruit_job = RecruitJob.objects.get(id=recruit_job_id)
        if recruit_job.description not in (None, "", "N/A"):
            logger.info("Job info already set for RecruitJob id %s, skipping.", recruit_job_id)
            return recruit_job.id
        generate_and_save_job_info(
            recruit_job.recruitment.company.name,
            recruit_job.recruitment,
            recruit_job.title,
            recruit_job
        )
        logger.info(f"Job info task executed for RecruitJob id {recruit_job_id}.")
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
