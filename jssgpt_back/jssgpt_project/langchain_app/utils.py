import os
import json
import re
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from .models import Company, RecruitJob, CoverLetterPrompt

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 가져오기
openai_api_key = os.getenv("OPENAI_API_KEY")

# OpenAI 설정
llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=openai_api_key)

def parse_response(response):
    """
    LangChain에서 반환된 문자열을 JSON으로 파싱합니다.
    """
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {}
    
def parse_company_info(response):
    """
    LangChain 응답을 문자열에서 딕셔너리로 변환합니다.
    숫자 및 구분자를 제거합니다.
    """
    parsed_response = {}
    try:
        lines = response.split("\n")
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                clean_key = key.lstrip("-* ").strip()
                parsed_response[clean_key] = value.strip()
    except Exception as e:
        print(f"[ERROR] Failed to parse LangChain response: {e}")
    return parsed_response

def parse_langchain_response(response):
    """
    LangChain 응답을 문자열에서 딕셔너리로 변환합니다.
    (키-값 및 목록 형태 처리 – 키 앞의 불필요한 서식 문자('-','*',공백 등)을 제거)
    """
    parsed_response = {}
    current_key = None
    current_value = []
    try:
        lines = response.splitlines()
        for line in lines:
            line = line.strip()
            if ":" in line and not line[0].isdigit():
                if current_key and current_value:
                    clean_key = re.sub(r'^[\-\*\s]+', '', current_key).strip()
                    parsed_response[clean_key] = " ".join(current_value).strip()
                current_key, value = line.split(":", 1)
                current_key = re.sub(r'^[\-\*\s]+', '', current_key).strip()
                current_value = [value.strip()]
            elif line.startswith(("-", "*", "1.", "2.", "3.")):
                current_value.append(line)
            elif line:
                current_value.append(line)
        if current_key and current_value:
            clean_key = re.sub(r'^[\-\*\s]+', '', current_key).strip()
            parsed_response[clean_key] = " ".join(current_value).strip()
    except Exception as e:
        print(f"[ERROR] Failed to parse LangChain response: {e}")
    return parsed_response

def generate_and_save_company_info(company_name):
    """
    기업 정보를 LangChain으로 생성하고 DB에 저장합니다.
    """
    prompt = f"""
    {company_name}에 대해 조사해줘. 다음 사항을 포함해서 알려줘:

    - 산업: 해당 기업이 속한 산업의 동향과 시장 상황.
    - 회사 비전: 회사가 추구하는 비전
    - 미션: 회사가 추구하는 사명, 핵심 가치.
    - 기업 문화와 인재상: 회사가 어떤 문화를 가지고 있으며, 어떤 유형의 인재를 중요하게 여기는지.
    - 최근 주요 성과: 최근에 회사가 이룬 업적이나 발표한 성장 지표, 수상 내역 등.
    - 현재 주요 이슈: 회사가 직면한 도전이나 업계의 이슈, 혹은 최신 뉴스.

    각 항목을 지원자가 자기소개서 작성 시 참고할 수 있도록 자세하고 명확하게 정리해줘.
    단, json 형식으로 출력해줘.
    """
    response = llm.predict(prompt)
    print(f"[DEBUG] LangChain Response for Company: {response}")
    parsed_response = parse_company_info(response)
    print(f"[DEBUG] Parsed Response for Company: {parsed_response}")
    company, created = Company.objects.get_or_create(name=company_name)
    company.industry = parsed_response.get("산업", "N/A")
    company.vision = parsed_response.get("회사 비전", "N/A")
    company.mission = parsed_response.get("미션", "N/A")
    company.core_values = parsed_response.get("기업 문화와 인재상", "N/A")
    company.recent_achievements = parsed_response.get("최근 주요 성과", "N/A")
    company.key_issues = parsed_response.get("현재 주요 이슈", "N/A")
    company.save()
    print(f"[DEBUG] Saved Company: {company}")
    return company

def generate_and_save_job_info(company_name, recruitment, job_title, recruit_job_instance):
    """
    회사명, 채용 공고, 직무명을 받아 LangChain을 통해 정보를 생성하고,
    기존 RecruitJob 인스턴스를 업데이트합니다.
    """
    prompt = f"""
    {company_name}의 {job_title} 직무에 대해 조사해줘. 아래 사항을 중심으로 자세히 알려줘:

    - 직무 설명: 해당 직무의 기본적인 역할과 책임이 무엇인지.
    - 수행 업무: 이 직무에서 일상적으로 수행하게 될 구체적인 업무 내용은 무엇인지.
    - 필요한 기술: 성공적인 업무 수행을 위해 필요한 전문 지식이나 기술, 자격 요건.
    - 관련 소프트 스킬: 해당 직무에서 특히 중요하게 평가되는 의사소통, 리더십 등 소프트 스킬들.
    - 필요 강점: 이 직무에서 두각을 나타내기 위해 요구되는 성향이나 강점들.

    위 정보를 정리할 때, 지원자가 자기소개서에 본인의 어떤 역량과 강점을 강조하면 좋을지도 함께 제안해줘.
    단, json형식으로 출력해줘.
    """
    response = llm.predict(prompt)
    print(f"[DEBUG] LangChain Response for Job: {response}")
    parsed_data = parse_langchain_response(response)
    print(f"[DEBUG] Parsed Response for Job: {parsed_data}")
    
    recruit_job_instance.description = parsed_data.get("직무 설명", "N/A")
    recruit_job_instance.required_skills = parsed_data.get("필요한 기술", "N/A")
    recruit_job_instance.soft_skills = parsed_data.get("관련 소프트 스킬", "N/A")
    recruit_job_instance.key_roles = parsed_data.get("수행 업무", "N/A")
    recruit_job_instance.related_technologies = parsed_data.get("필요 강점", "N/A")
    recruit_job_instance.save()
    print(f"[DEBUG] Updated Job Info: {recruit_job_instance.title}")
    return recruit_job_instance

def generate_and_save_cover_letter_outline(prompt_instance):
    """
    주어진 CoverLetterPrompt 인스턴스에 대해, LLM을 호출하여 자기소개서 문항 개요(outline)를 생성하고 DB에 저장합니다.
    각 prompt 인스턴스마다 개별적으로 outline을 생성하며, 기존 인스턴스는 새로 생성하지 않고 업데이트합니다.
    """
    if prompt_instance.outline:
        print(f"[DEBUG] CoverLetterOutline already exists for prompt id: {prompt_instance.id}")
        return prompt_instance

    prompt_text = f"""
    이제 채용 회사와 직무 정보를 바탕으로 자기소개서의 전체 **개요(아웃라인)**를 만들어줘. 우선 자기소개서 문항들을 파악해야 해.

    자기소개서 문항:  
    {prompt_instance.question_text}

    이제 각 문항에 대해 답변의 개요를 작성해줘. 개요에는 다음 내용이 들어가면 좋겠어:

    - 핵심 주제: 해당 문항에서 강조해야 할 내용이 무엇인지 한 문장으로 요약 (예: 지원 동기에서는 왜 이 회사인지에 대한 설명).
    - 포함할 키워드: 회사 조사와 직무 조사에서 찾은 관련 키워드나 개념 중 해당 문항에 넣으면 좋은 것.
    - 경험 사례 연결: 답변에 활용할 만한 지원자의 경험이나 역량 (현재 단계에서 지원자 경험 정보가 없으면 일반적인 예시로 적어줘. 만약 지원자 경험이 주어져 있다면 그 중 어떤 것을 사용할지 제안).

    각 문항별로 bullet point 형태로 개요를 제시해줘. 이 개요는 나중에 실제 자기소개서 답안을 작성할 때 가이드라인이 될 거야.
    동시에 개요에는 다음 내용을 유의하여 작성해줘.
    1. 한 문항에는 하나의 경험만 서술할 것.
    2. 같은 {prompt_instance.recruit_job}의 자기소개서를 작성할 때, 문항들이 각기 다른 경험, 역량을 강조할 수 있도록 개요를 작성할 것.
    """
    outline = llm.predict(prompt_text)
    prompt_instance.outline = outline
    prompt_instance.save()
    print(f"[DEBUG] Generated and saved Cover Letter Outline for prompt id: {prompt_instance.id}")
    return prompt_instance
