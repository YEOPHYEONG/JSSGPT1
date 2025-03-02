# langchain_app/views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import (
    generate_and_save_company_info,
    generate_and_save_job_info,
    generate_and_save_cover_letter_outline,
)
from .models import Recruitment
from django.shortcuts import get_object_or_404

@csrf_exempt
def create_recruitment(request):
    try:
        # JSON 데이터 파싱
        data = json.loads(request.body)
        
        # 필수 필드 검증
        required_fields = ["company_name", "start_date", "end_date", "job_titles"]
        for field in required_fields:
            if field not in data:
                return JsonResponse({"error": f"필드 {field}가 필요합니다."}, status=400)
        
        company_name = data["company_name"]

        # 1. 기업 정보 생성
        company = generate_and_save_company_info(company_name)

        # 2. 채용공고 생성
        recruitment = Recruitment.objects.create(
            company=company,
            title=f"{company_name} 채용 공고",
            start_date=data["start_date"],
            end_date=data["end_date"],
        )

        # 3. 직무 및 문항 처리
        for job in data["job_titles"]:
            job_title = job["title"]
            questions = job["questions"]

            # 직무 정보 생성 및 저장
            recruit_job = generate_and_save_job_info(company_name, recruitment, job_title)

            # 자기소개서 문항 처리 및 저장
            for question in questions:
                generate_and_save_cover_letter_outline(recruit_job, question)

        return JsonResponse({"success": "채용 공고가 성공적으로 생성되었습니다."})

    except json.JSONDecodeError:
        return JsonResponse({"error": "잘못된 JSON 형식입니다."}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"예상치 못한 오류: {str(e)}"}, status=500)


def get_recruitment_events(request):
    """
    모든 Recruitment 객체를 가져와서 JSON 리스트로 반환합니다.
    (실제 개발 시에는 날짜별 필터링 등 추가 기능을 구현할 수 있습니다.)
    """
    events = Recruitment.objects.select_related('company').all()
    event_list = []
    for event in events:
        event_list.append({
            "recruitment_id": event.id,  # 또는 event.custom_id 사용 가능
            "recruitment_title": event.title,
            "start_date": event.start_date.isoformat(),
            "end_date": event.end_date.isoformat(),
            "company_name": event.company.name,
            "jss_link": event.jss_link,
            "recruitment_link": event.recruitment_link,
        })
    return JsonResponse(event_list, safe=False)

def get_recruitment_detail(request, id):
    """
    Recruitment 상세 정보를 반환합니다.
    Recruitment와 연결된 모든 RecruitJob과 각 RecruitJob에 연결된 CoverLetterPrompt (자기소개서 문항)을 포함합니다.
    """
    # select_related와 prefetch_related를 사용해 관련 데이터를 미리 로드합니다.
    recruitment = get_object_or_404(
        Recruitment.objects.select_related('company').prefetch_related('recruit_jobs__cover_letter_prompts'),
        id=id
    )
    recruitments_data = []
    for job in recruitment.recruit_jobs.all():
        essays = []
        for prompt in job.cover_letter_prompts.all():
            essays.append({
                "id": prompt.id,  # 질문의 id 추가
                "question_text": prompt.question_text,
                "limit": prompt.limit,
            })
        recruitments_data.append({
            "id": job.id,
            "title": job.title,
            "type": job.recruitment_type,
            "link": "",  # RecruitJob 모델에 link 필드가 없다면 빈 문자열로 처리하거나, 필요한 필드를 추가하세요.
            "essays": essays,
        })
    data = {
        "recruitment_id": recruitment.id,
        "recruitment_title": recruitment.title,
        "start_date": recruitment.start_date.isoformat(),
        "end_date": recruitment.end_date.isoformat(),
        "company_name": recruitment.company.name,
        "jss_link": recruitment.jss_link,
        "recruitment_link": recruitment.recruitment_link,
        "recruitments": recruitments_data,
    }
    return JsonResponse(data)
