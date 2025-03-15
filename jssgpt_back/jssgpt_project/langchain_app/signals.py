import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Company, RecruitJob, CoverLetterPrompt
from .tasks import generate_company_info_task, generate_job_info_task, generate_outline_task_for_prompt

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Company)
def company_post_save(sender, instance, created, **kwargs):
    # 수정: industry가 None 또는 빈 문자열일 경우에만 태스크 호출
    if created or instance.industry in (None, ""):
        transaction.on_commit(lambda: generate_company_info_task.delay(instance.id))
        logger.info("Enqueued company info task for Company id %s", instance.id)

@receiver(post_save, sender=RecruitJob)
def recruitjob_post_save(sender, instance, created, **kwargs):
    # 수정: description이 None 또는 빈 문자열일 경우에만 태스크 호출
    if created or instance.description in (None, ""):
        transaction.on_commit(lambda: generate_job_info_task.delay(instance.id))
        logger.info("Enqueued job info task for RecruitJob id %s", instance.id)

@receiver(post_save, sender=CoverLetterPrompt)
def coverletterprompt_post_save(sender, instance, created, **kwargs):
    # 이미 존재하는 CoverLetterPrompt 인스턴스의 outline이 비어있다면 개별 태스크를 등록합니다.
    if created and not instance.outline:
        transaction.on_commit(lambda: generate_outline_task_for_prompt.delay(instance.id))
        logger.info("Enqueued outline task for CoverLetterPrompt id %s", instance.id)