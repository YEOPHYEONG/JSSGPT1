# langchain_app/tasks.py
import os
import sys
import subprocess
import json
import logging
from celery import shared_task
from django.conf import settings  # Django의 settings 모듈 사용
from .models import Company, RecruitJob
from .utils import (
    generate_and_save_company_info,
    generate_and_save_job_info,
    generate_and_save_cover_letter_outline,
)
from .utils_crawler import save_crawled_json_data
from pathlib import Path

logger = logging.getLogger(__name__)

@shared_task
def crawl_recruitments_task(target_date_str):
    logger.info("Current working directory in tasks.py: %s", os.getcwd())
    
    # BASE_DIR가 langchain_app 폴더라면, 그 부모 폴더가 프로젝트 루트입니다.
    base_dir = str(Path(__file__).resolve().parent.parent)
    crawler_script_path = os.path.join(base_dir, "crawler_script.py")
    
    # 디버깅 로그
    logger.info("settings.BASE_DIR: %s", settings.BASE_DIR)
    logger.info("Calculated project root (base_dir): %s", base_dir)
    logger.info("crawler_script_path: %s", crawler_script_path)
    
    cwd = base_dir  # 작업 디렉터리를 프로젝트 루트로 지정
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
        company = Company.objects.get(id=company_id)
        # 이미 회사 정보가 채워졌다면 작업 건너뛰기 (예: industry가 "N/A"가 아닐 경우)
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
        recruit_job = RecruitJob.objects.get(id=recruit_job_id)
        # 이미 직무 정보가 채워졌다면 (description이 "N/A"가 아니라면) 작업 건너뛰기
        if recruit_job.description not in (None, "", "N/A"):
            logger.info("Job info already set for RecruitJob id %s, skipping.", recruit_job_id)
            return recruit_job.id
        generate_and_save_job_info(
            recruit_job.recruitment.company.name,
            recruit_job.recruitment,
            recruit_job.title,
            recruit_job  # 4번째 인자로 실제 인스턴스를 전달합니다.
        )
        logger.info(f"Job info task executed for RecruitJob id {recruit_job_id}.")
    except RecruitJob.DoesNotExist:
        logger.error(f"RecruitJob id {recruit_job_id} not found.")
        return "RecruitJob not found."

@shared_task
def generate_outline_task(recruit_job_id, question):
    try:
        recruit_job = RecruitJob.objects.get(id=recruit_job_id)
        # outline이 채워져 있다면 건너뛰기
        if recruit_job.cover_letter_prompts.filter(outline__isnull=False).exists():
            logger.info("Outline already generated for RecruitJob id %s, skipping.", recruit_job_id)
            return recruit_job.id
        generate_and_save_cover_letter_outline(recruit_job, question)
        logger.info(f"Outline task executed for RecruitJob id {recruit_job_id} with question: {question}")
    except RecruitJob.DoesNotExist:
        logger.error(f"RecruitJob id {recruit_job_id} not found.")
        return "RecruitJob not found."
