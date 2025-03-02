# langchain_app/tasks.py
from celery import shared_task
from .models import Company, RecruitJob
from .utils import generate_and_save_company_info, generate_and_save_job_info, generate_and_save_cover_letter_outline

@shared_task
def generate_company_info_task(company_id):
    try:
        company = Company.objects.get(id=company_id)
        generate_and_save_company_info(company.name)
    except Company.DoesNotExist:
        return "Company not found."

@shared_task
def generate_job_info_task(recruit_job_id):
    try:
        recruit_job = RecruitJob.objects.get(id=recruit_job_id)
        generate_and_save_job_info(
            recruit_job.recruitment.company.name,
            recruit_job.recruitment,
            recruit_job.title
        )
    except RecruitJob.DoesNotExist:
        return "RecruitJob not found."

@shared_task
def generate_outline_task(recruit_job_id, question):
    try:
        recruit_job = RecruitJob.objects.get(id=recruit_job_id)
        generate_and_save_cover_letter_outline(recruit_job, question)
    except RecruitJob.DoesNotExist:
        return "RecruitJob not found."
