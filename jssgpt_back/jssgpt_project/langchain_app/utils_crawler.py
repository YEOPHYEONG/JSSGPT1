# langchain_app/utils_crawler.py
import datetime
from .models import Company, Recruitment, RecruitJob, CoverLetterPrompt

def parse_start_date(date_str):
    """
    YYYYMMDD 형식 문자열을 datetime.date 객체로 변환
    """
    try:
        return datetime.datetime.strptime(date_str, "%Y%m%d").date()
    except Exception as e:
        print(f"[ERROR] start_date 파싱 실패: {e}")
        return None

def parse_end_date(date_str):
    """
    "2025년 3월 16일 14:59" 형식의 문자열에서 날짜 부분만 파싱하여 datetime.date 객체로 변환.
    파싱 실패 시 None 반환.
    """
    try:
        # 공백을 기준으로 날짜 부분만 사용 (예: "2025년 3월 16일")
        date_part = date_str.split(" ")[0]
        return datetime.datetime.strptime(date_part, "%Y년 %m월 %d일").date()
    except Exception as e:
        print(f"[ERROR] end_date 파싱 실패: {e}")
        return None

def parse_limit(limit_str):
    """
    (700자)와 같이 들어온 문자열에서 숫자만 추출하여 정수로 반환.
    """
    try:
        cleaned = limit_str.replace("(", "").replace(")", "").replace("자", "").strip()
        return int(cleaned)
    except Exception as e:
        print(f"[ERROR] limit 파싱 실패: {e}")
        return None

def save_crawled_json_data(data_list):
    """
    크롤러가 반환한 JSON 데이터 리스트(data_list)를 받아
    Company, Recruitment, RecruitJob, CoverLetterPrompt 모델에 매핑하여 DB에 저장하는 함수.
    매핑:
      - Recruitment.start_date <- JSON["start_date"]
      - Recruitment.custom_id <- JSON["employment_id"]
      - Recruitment.jss_link <- JSON["link"]
      - Recruitment.end_date <- JSON["end_date"] (파싱 실패 시 None)
      - Recruitment.recruitment_link <- JSON["recruitment_link"]
      - Company.name <- JSON["company_name"]
      - 각 RecruitJob:
            recruitment_type <- job["recruitment_type"]
            title <- job["recruitment_title"]
      - 각 CoverLetterPrompt:
            question_text <- essay["question"]
            limit <- essay["limit"]
    """
    for comp in data_list:
        # Parse 날짜들
        start_date = parse_start_date(comp.get("start_date"))
        end_date = parse_end_date(comp.get("end_date")) if comp.get("end_date") else None
        
        company_name = comp.get("company_name")
        if not company_name:
            print("[ERROR] company_name이 없습니다.")
            continue
        
        # Company 생성 (또는 가져오기)
        company, _ = Company.objects.get_or_create(name=company_name)
        
        # Recruitment 생성
        recruitment = Recruitment.objects.create(
            company=company,
            title=f"{company_name} 채용 공고",  # 기본 제목 처리 (필요 시 수정)
            start_date=start_date if start_date else datetime.date.today(),
            end_date=end_date,  # 파싱 실패 시 None 가능
            recruitment_link=comp.get("recruitment_link"),
            jss_link=comp.get("link")
        )
        # JSON의 employment_id를 Recruitment.custom_id로 저장
        employment_id = comp.get("employment_id")
        if employment_id:
            recruitment.custom_id = employment_id
            recruitment.save()
        
        print(f"[INFO] Created Recruitment: {recruitment}")
        
        # 각 직무 처리
        jobs = comp.get("jobs", [])
        for job_data in jobs:
            recruit_job = RecruitJob.objects.create(
                recruitment=recruitment,
                title=job_data.get("recruitment_title"),
                recruitment_type=job_data.get("recruitment_type")
            )
            print(f"[INFO] Created RecruitJob: {recruit_job}")
            
            # 각 자기소개서 문항 처리
            essay_questions = job_data.get("essay_questions", [])
            for essay in essay_questions:
                question_text = essay.get("question")
                limit_str = essay.get("limit")
                limit = parse_limit(limit_str) if limit_str else None
                cover_letter_prompt = CoverLetterPrompt.objects.create(
                    recruit_job=recruit_job,
                    question_text=question_text,
                    limit=limit
                )
                print(f"[INFO] Created CoverLetterPrompt: {cover_letter_prompt}")
