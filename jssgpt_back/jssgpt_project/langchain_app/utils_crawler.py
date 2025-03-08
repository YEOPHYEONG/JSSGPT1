import datetime
from .models import Company, Recruitment, RecruitJob, CoverLetterPrompt

def parse_start_date(date_str):
    """
    YYYYMMDD 형식 문자열을 datetime.date 객체로 변환합니다.
    """
    try:
        return datetime.datetime.strptime(date_str, "%Y%m%d").date()
    except Exception as e:
        print(f"[ERROR] start_date 파싱 실패: {e}")
        return None

def parse_end_date(date_str):
    """
    "2025년 3월 16일 14:59" 형식의 문자열에서 날짜 부분(예: "2025년 3월 16일")을 파싱하여
    datetime.date 객체로 변환합니다.
    만약 날짜에 월과 일이 모두 포함되어 있지 않으면 None을 반환합니다.
    """
    if not date_str or date_str.strip() == "~":
        return None
    parts = date_str.split(" ")
    if len(parts) < 2:
        # 예: "2025년"만 있는 경우
        return None
    date_part = parts[0]
    try:
        return datetime.datetime.strptime(date_part, "%Y년 %m월 %d일").date()
    except Exception as e:
        print(f"[ERROR] end_date 파싱 실패: {e}")
        return None

def parse_limit(limit_str):
    """
    "(700자)"와 같이 들어온 문자열에서 숫자만 추출하여 정수로 반환합니다.
    """
    try:
        cleaned = limit_str.replace("(", "").replace(")", "").replace("자", "").strip()
        return int(cleaned)
    except Exception as e:
        print(f"[ERROR] limit 파싱 실패: {e}")
        return None

def save_crawled_json_data(data_list):
    """
    크롤러가 반환한 JSON 데이터 리스트(data_list)를 받아서,
    Company, Recruitment, RecruitJob, CoverLetterPrompt 모델에 매핑하여 DB에 저장합니다.
    
    - start_date는 YYYYMMDD 형식으로 파싱합니다.
    - end_date는 "YYYY년 MM월 DD일 ..." 형식으로 파싱을 시도하며, 실패 시 None을 반환합니다.
      이 경우 start_date가 유효하면 기본값으로 start_date + 7일을 사용합니다.
    """
    for comp in data_list:
        try:
            # 날짜 파싱
            start_date = parse_start_date(comp.get("start_date"))
            end_date = None
            if comp.get("end_date"):
                end_date = parse_end_date(comp.get("end_date"))
            
            # end_date가 파싱되지 않았으면, start_date가 있다면 기본값으로 start_date + 7일을 사용
            if end_date is None and start_date is not None:
                end_date = start_date + datetime.timedelta(days=7)

            company_name = comp.get("company_name")
            if not company_name:
                print("[ERROR] company_name이 없습니다.")
                continue

            print(f"[DEBUG] 저장할 회사 이름: {company_name}")
            # Company 객체 생성 또는 기존 객체 사용
            company, created = Company.objects.get_or_create(name=company_name)
            if created:
                print(f"[DEBUG] 새로운 Company 생성됨: {company}")
            else:
                print(f"[DEBUG] 기존 Company 사용: {company}")

            # Recruitment 객체 생성
            # Recruitment 모델의 end_date 필드는 DB에 저장 시 유효한 날짜여야 합니다.
            recruitment = Recruitment.objects.create(
                company=company,
                title=f"{company_name} 채용 공고",
                start_date=start_date if start_date else datetime.date.today(),
                end_date=end_date,
                recruitment_link=comp.get("recruitment_link"),
                jss_link=comp.get("link")
            )
            employment_id = comp.get("employment_id")
            if employment_id:
                recruitment.custom_id = employment_id
                recruitment.save()
            print(f"[INFO] Created Recruitment: {recruitment}")

            # 각 직무 처리
            jobs = comp.get("jobs", [])
            for job_data in jobs:
                try:
                    recruit_job = RecruitJob.objects.create(
                        recruitment=recruitment,
                        title=job_data.get("recruitment_title"),
                        recruitment_type=job_data.get("recruitment_type")
                    )
                    print(f"[INFO] Created RecruitJob: {recruit_job}")
                except Exception as je:
                    print(f"[ERROR] RecruitJob 생성 실패: {je}")
                    continue

                # 각 자기소개서 문항 처리
                essay_questions = job_data.get("essay_questions", [])
                for essay in essay_questions:
                    try:
                        question_text = essay.get("question")
                        limit_str = essay.get("limit")
                        limit = parse_limit(limit_str) if limit_str else None
                        cover_letter_prompt = CoverLetterPrompt.objects.create(
                            recruit_job=recruit_job,
                            question_text=question_text,
                            limit=limit
                        )
                        print(f"[INFO] Created CoverLetterPrompt: {cover_letter_prompt}")
                    except Exception as ce:
                        print(f"[ERROR] CoverLetterPrompt 생성 실패: {ce}")
        except Exception as e:
            print(f"[ERROR] 전체 저장 과정에서 예외 발생: {e}")
