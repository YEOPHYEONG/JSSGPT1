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
    if created:
        transaction.on_commit(lambda: generate_company_info_task.delay(instance.id))
        logger.info("Enqueued company info task for Company id %s", instance.id)

@receiver(post_save, sender=RecruitJob)
def recruitjob_post_save(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(lambda: generate_job_info_task.delay(instance.id))
        logger.info("Enqueued job info task for RecruitJob id %s", instance.id)

@receiver(post_save, sender=CoverLetterPrompt)
def coverletterprompt_post_save(sender, instance, created, **kwargs):
    # outline 필드가 아직 채워지지 않은 경우에만 LLM 작업 실행
    if created and not instance.outline:
        transaction.on_commit(lambda: generate_outline_task.delay(instance.recruit_job.id, instance.question_text))
        logger.info("Enqueued outline task for CoverLetterPrompt id %s (RecruitJob id %s)", instance.id, instance.recruit_job.id)
