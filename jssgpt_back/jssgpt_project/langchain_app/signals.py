# langchain_app/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Company, RecruitJob, CoverLetterPrompt
from .tasks import generate_company_info_task, generate_job_info_task, generate_outline_task

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Company)
def company_post_save(sender, instance, created, **kwargs):
    # 이미 회사 정보가 처리되었다면 (예: industry 필드가 "N/A"가 아니면) 작업을 건너뜁니다.
    if created or instance.industry in (None, "", "N/A"):
        transaction.on_commit(lambda: generate_company_info_task.delay(instance.id))
        logger.info("Enqueued company info task for Company id %s", instance.id)

@receiver(post_save, sender=RecruitJob)
def recruitjob_post_save(sender, instance, created, **kwargs):
    # 이미 직무 정보가 처리되었다면 (예: description 필드가 "N/A"가 아니면) 작업을 건너뜁니다.
    if created or instance.description in (None, "", "N/A"):
        transaction.on_commit(lambda: generate_job_info_task.delay(instance.id))
        logger.info("Enqueued job info task for RecruitJob id %s", instance.id)

@receiver(post_save, sender=CoverLetterPrompt)
def coverletterprompt_post_save(sender, instance, created, **kwargs):
    # outline 필드가 채워져 있다면 이미 처리된 것으로 간주합니다.
    if created and not instance.outline:
        transaction.on_commit(lambda: generate_outline_task.delay(instance.recruit_job.id, instance.question_text))
        logger.info("Enqueued outline task for CoverLetterPrompt id %s (RecruitJob id %s)", instance.id, instance.recruit_job.id)
