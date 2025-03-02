import os
import json
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from .models import Company, RecruitJob, CoverLetterPrompt

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 가져오기
openai_api_key = os.getenv("OPENAI_API_KEY")

# OpenAI 설정
llm = ChatOpenAI(model="gpt-4", temperature=0, openai_api_key=openai_api_key)

def parse_response(response):
    """
    LangChain에서 반환된 문자열을 JSON으로 파싱
    """
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {}
    
def parse_company_info(response):
    """
    LangChain 응답을 문자열에서 딕셔너리로 변환 (숫자/구분자 제거)
    """
    parsed_response = {}
    try:
        lines = response.split("\n")
        for line in lines:
            if ":" in line:  # 키-값 구분
                key, value = line.split(":", 1)
                clean_key = key.strip().lstrip("0123456789.").strip()  # 숫자 및 구분자 제거
                parsed_response[clean_key] = value.strip()
    except Exception as e:
        print(f"[ERROR] Failed to parse LangChain response: {e}")
    return parsed_response


def parse_langchain_response(response):
    """
    LangChain 응답을 문자열에서 딕셔너리로 변환 (키-값 및 목록 형태 처리)
    """
    parsed_response = {}
    current_key = None
    current_value = []

    try:
        lines = response.split("\n")
        for line in lines:
            line = line.strip()

            # 키-값 구분 (':' 포함된 경우)
            if ":" in line and not line[0].isdigit():  # 숫자로 시작하지 않는 경우
                if current_key and current_value:
                    # 이전 키 저장
                    parsed_response[current_key] = "\n".join(current_value).strip()
                current_key, value = line.split(":", 1)
                current_key = current_key.strip()
                current_value = [value.strip()]
            # 목록 처리 (숫자나 '-'로 시작하는 경우)
            elif line.startswith(("1.", "2.", "3.", "-")):
                current_value.append(line)
            # 빈 줄 처리 (값 추가)
            elif line:
                current_value.append(line)

        # 마지막 키 저장
        if current_key and current_value:
            parsed_response[current_key] = "\n".join(current_value).strip()

    except Exception as e:
        print(f"[ERROR] Failed to parse LangChain response: {e}")

    return parsed_response

def generate_and_save_company_info(company_name):
    """
    기업 정보를 LangChain으로 생성하고 DB에 저장
    """
    prompt = f"{company_name}의 산업, 비전, 미션, 인재상, 최근 성과, 주요 이슈에 대해서 자세하게 조사해줘."
    response = llm.predict(prompt)

    # 디버깅 로그
    print(f"[DEBUG] LangChain Response for Company: {response}")

    # 응답 파싱
    parsed_response = parse_company_info(response)
    print(f"[DEBUG] Parsed Response for Company: {parsed_response}")

    # 데이터 저장
    company, created = Company.objects.get_or_create(name=company_name)
    company.industry = parsed_response.get("산업", "N/A")
    company.vision = parsed_response.get("비전", "N/A")
    company.mission = parsed_response.get("미션", "N/A")
    company.core_values = parsed_response.get("핵심 가치", "N/A")
    company.recent_achievements = parsed_response.get("최근 성과", "N/A")
    company.key_issues = parsed_response.get("주요 이슈", "N/A")
    company.save()

    print(f"[DEBUG] Saved Company: {company}")
    return company

def generate_and_save_job_info(company_name, recruitment, job_title):
    """
    회사명, 채용 공고, 직무명을 받아 LangChain을 통해 정보를 생성하고 저장
    """
    prompt = f"""
    {company_name}의 {job_title}의 기본 설명, 수행 업무, 직무 요구 역량, 직무 관련 소프트 스킬, 필요 강점에 대해서 자세하게 조사해줘.
    """
    response = llm.predict(prompt)
    print(f"[DEBUG] LangChain Response for Job: {response}")

    # 개선된 파싱 함수 적용
    parsed_data = parse_langchain_response(response)
    print(f"[DEBUG] Parsed Response for Job: {parsed_data}")

    # 데이터 저장
    job = RecruitJob.objects.create(
        recruitment=recruitment,
        title=job_title,
        description=parsed_data.get("직무 설명", "N/A"),
        required_skills=parsed_data.get("필요한 기술", "N/A"),
        soft_skills=parsed_data.get("관련 소프트 스킬", "N/A"),
        key_roles=parsed_data.get("핵심 역할", "N/A"),
        related_technologies=parsed_data.get("관련 기술", "N/A")
    )

    print(f"[DEBUG] Saved Job Info: {job.title}")
    return job

def generate_and_save_cover_letter_outline(job, question):
    # 자기소개서 문항 개요 생성 및 저장
    prompt = f"""
    다음은 {question}이야. 인지해둬.

    나는 {job.recruitment.company.name}의 {job.title}에 지원하려고 해.

    자기소개서를 잘 쓰는 방법을 바탕으로 기업과 직무에 대한 정보가 주어진 상황에서
    다음 자기소개서가 잘 쓰여지기 위한 각 문항의 개요를 작성해줘.
    개요에는 다음 내용을 포함하여 작성해줘:
    1. 방향성
    2. 해당 기업과 직무에서 강조해야 할 역량 1개
    3. 서론, 본론, 결론에 들어가야하는 해당 기업과 직무에 적합한 주요 내용의 키워드 3개
    동시에 개요에는 다음 내용을 유의하여 작성해줘.
    1. 한 문항에는 하나의 경험만 서술할 것.
    2. 같은 {RecruitJob}의 자기소개서를 작성할 때, 동일한 경험, 역량, 방향성 등이 겹치지 않게, 개요를 작성할 것.
    """
    outline = llm.predict(prompt)

    cover_letter_prompt = CoverLetterPrompt.objects.create(
        recruit_job=job,
        question_text=question,
        outline=outline,
    )

    print(f"[DEBUG] Saved Cover Letter Outline: {question}")
    return cover_letter_prompt
