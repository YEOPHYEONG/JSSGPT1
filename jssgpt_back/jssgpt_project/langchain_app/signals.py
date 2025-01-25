from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Company, Recruitment, RecruitJob, CoverLetterPrompt
from .utils import generate_and_save_company_info, generate_and_save_job_info, generate_and_save_cover_letter_outline

@receiver(post_save, sender=Recruitment)
def handle_new_recruitment(sender, instance, created, **kwargs):
    if not created:
        return  # 수정된 경우 작업하지 않음

    print(f"[DEBUG] Recruitment Created: {instance}")

    # 1. 기업 정보 확인 및 생성
    company, created = Company.objects.get_or_create(name=instance.company.name)
    if created:
        generate_and_save_company_info(company)

    # 2. 채용 직무 생성 및 정보 저장
    for job_data in instance.job_titles:  # job_titles는 입력 데이터에서 전달받음
        job = generate_and_save_job_info(
            instance.company.name,
            instance,
            job_data["title"]
        )

        # 3. 자기소개서 문항 생성
        for question in job_data.get("questions", []):
            generate_and_save_cover_letter_outline(job, question)
