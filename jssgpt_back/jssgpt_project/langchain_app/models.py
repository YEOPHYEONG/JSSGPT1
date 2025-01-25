from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)  # 기업명
    industry = models.CharField(max_length=255, null=True, blank=True)  # 산업
    vision = models.TextField(null=True, blank=True)  # 비전
    mission = models.TextField(null=True, blank=True)  # 미션
    core_values = models.TextField(null=True, blank=True)  # 핵심 가치
    recent_achievements = models.TextField(null=True, blank=True)  # 최근 성과
    key_issues = models.TextField(null=True, blank=True)  # 주요 이슈

    def __str__(self):
        return self.name


class Recruitment(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='recruitments')
    title = models.CharField(max_length=255)  # 채용공고 제목
    start_date = models.DateField()  # 채용 시작일
    end_date = models.DateField()  # 채용 종료일
    notes = models.TextField(null=True, blank=True)  # 직무 및 문항 데이터 저장용
    custom_id = models.CharField(max_length=255, unique=True, editable=False, null=True)  # 채용 공고 ID

    def save(self, *args, **kwargs):
        # 기업명과 순번 기반으로 custom_id 생성
        if not self.custom_id:
            count = Recruitment.objects.filter(company=self.company).count() + 1
            self.custom_id = f"{self.company.name}-{count}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.custom_id}: {self.title}"


class RecruitJob(models.Model):
    recruitment = models.ForeignKey(Recruitment, on_delete=models.CASCADE, related_name='recruit_jobs')
    title = models.CharField(max_length=255)  # 직무명
    description = models.TextField(null=True, blank=True)  # 직무 설명
    key_roles = models.TextField(null=True, blank=True)  # 핵심 역할
    required_skills = models.TextField(null=True, blank=True)  # 요구 역량
    related_technologies = models.TextField(null=True, blank=True)  # 직무 관련 기술
    soft_skills = models.TextField(null=True, blank=True)  # 소프트 스킬
    key_strengths = models.TextField(null=True, blank=True)  # 필요 강점

    def __str__(self):
        return f"{self.recruitment.title} - {self.title}"


class CoverLetterPrompt(models.Model):
    recruit_job = models.ForeignKey(RecruitJob, on_delete=models.CASCADE, related_name='cover_letter_prompts')
    question_text = models.TextField()  # 자기소개서 문항
    outline = models.TextField(null=True, blank=True)  # AI가 생성한 개요
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시각
    updated_at = models.DateTimeField(auto_now=True)  # 수정 시각

    def __str__(self):
        return f"{self.recruit_job.title} - {self.question_text}"


class CoverLetterGuide(models.Model):
    title = models.CharField(max_length=255)  # 지침 제목
    content = models.TextField()  # 자기소개서 작성 방법에 대한 상세 내용
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시간
    updated_at = models.DateTimeField(auto_now=True)  # 수정 시간

    def __str__(self):
        return self.title
