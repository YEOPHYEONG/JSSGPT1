import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import generate_and_save_company_info, generate_and_save_job_info, generate_and_save_cover_letter_outline
from .models import Recruitment

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
