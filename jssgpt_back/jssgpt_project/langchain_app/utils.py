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
llm = ChatOpenAI(model="gpt-4o-2024-11-20", temperature=0, openai_api_key=openai_api_key)
search_llm = ChatOpenAI(model="gpt-4o-search-preview-2025-03-11", temperature=None, openai_api_key=openai_api_key)

def clean_json_response(response):
    """
    응답 문자열에서 Markdown 코드 블록 및 불필요한 문구를 제거합니다.
    예) "```json" 및 "```" 제거
    """
    cleaned = response.strip()
    # 코드 블록 시작 및 끝 제거 (대소문자 무관)
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned

def parse_response(response):
    """
    응답 문자열을 정리한 후 JSON으로 파싱합니다.
    """
    cleaned = clean_json_response(response)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print("[ERROR] JSONDecodeError in parse_response")
        return {}

def flatten_json(data):
    """
    중첩된 JSON 딕셔너리를 평탄화합니다.
    예) {"직무 설명": {"역할": "A", "책임": "B"}}
         -> {"직무 설명": "역할: A, 책임: B"}
    """
    flattened = {}
    for key, value in data.items():
        if isinstance(value, dict):
            inner_parts = []
            for subkey, subvalue in value.items():
                # 만약 내부 값이 리스트라면 join 처리
                if isinstance(subvalue, list):
                    subvalue = ", ".join(map(str, subvalue))
                inner_parts.append(f"{subkey}: {subvalue}")
            flattened[key] = ", ".join(inner_parts)
        elif isinstance(value, list):
            flattened[key] = ", ".join(map(str, value))
        else:
            flattened[key] = value
    return flattened

def parse_company_info(response):
    """
    LangChain 응답을 정리하고, JSON 파싱 후 평탄화합니다.
    JSON 파싱에 실패하면 fallback 방식으로 라인 단위 파싱을 사용합니다.
    만약 최상위 JSON 딕셔너리에 단일 키가 있고 그 값이 dict이면, 그 내부 딕셔너리를 사용합니다.
    """
    cleaned = clean_json_response(response)
    try:
        data = json.loads(cleaned)
        # 최상위 딕셔너리에 단일 키가 있고, 해당 값이 dict인 경우 내부로 이동
        if isinstance(data, dict) and len(data) == 1:
            inner = list(data.values())[0]
            if isinstance(inner, dict):
                data = inner

        # JSON 평탄화
        flattened = flatten_json(data)

        # 언더바를 공백으로 치환하여 키 정규화
        normalized = {k.replace("_", " "): v for k, v in flattened.items()}

        return normalized

    except json.JSONDecodeError:
        parsed_response = {}
        try:
            lines = cleaned.split("\n")
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    clean_key = key.lstrip("-* ").strip().strip('"')
                    parsed_response[clean_key] = value.strip().strip('"')
        except Exception as e:
            print(f"[ERROR] Failed to parse LangChain response: {e}")

        # 라인 단위 파싱 결과에도 언더바 -> 공백 치환
        return {k.replace("_", " "): v for k, v in parsed_response.items()}

def parse_langchain_response(response):
    """
    LangChain 응답을 정리하고, JSON 파싱 후 평탄화합니다.
    파싱에 성공하면, 키의 언더바("_")를 공백(" ")으로 치환하여 반환합니다.
    JSON 파싱에 실패하면, 기존 문자열 기반 파싱 방식을 사용하고 동일하게 키를 정규화합니다.
    """
    cleaned = clean_json_response(response)
    try:
        data = json.loads(cleaned)
        flattened = flatten_json(data)
        # 언더바를 공백으로 치환하여 키 정규화
        normalized = { k.replace("_", " "): v for k, v in flattened.items() }
        return normalized
    except json.JSONDecodeError:
        parsed_response = {}
        current_key = None
        current_value = []
        try:
            lines = cleaned.splitlines()
            for line in lines:
                line = line.strip()
                if ":" in line and not line[0].isdigit():
                    if current_key and current_value:
                        clean_key = re.sub(r'^[\-\*\s]+', '', current_key).strip().strip('"')
                        parsed_response[clean_key] = " ".join(current_value).strip().strip('"')
                    current_key, value = line.split(":", 1)
                    current_key = re.sub(r'^[\-\*\s]+', '', current_key).strip().strip('"')
                    current_value = [value.strip().strip('"')]
                elif line.startswith(("-", "*", "1.", "2.", "3.")):
                    current_value.append(line.strip().strip('"'))
                elif line:
                    current_value.append(line.strip().strip('"'))
            if current_key and current_value:
                clean_key = re.sub(r'^[\-\*\s]+', '', current_key).strip().strip('"')
                parsed_response[clean_key] = " ".join(current_value).strip().strip('"')
            # 언더바를 공백으로 치환하여 키 정규화
            normalized = { k.replace("_", " "): v for k, v in parsed_response.items() }
            return normalized
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
    주어진 CoverLetterPrompt 인스턴스에 대해, LLM을 호출하여
    채용 회사 및 직무 정보를 포함한 자기소개서 문항 개요(outline)를 생성하고 DB에 저장합니다.
    만약 이미 개요가 생성되어 있다면, 기존 개요를 그대로 반환합니다.
    """
    if prompt_instance.outline:
        print(f"[DEBUG] CoverLetterOutline already exists for prompt id: {prompt_instance.id}")
        return prompt_instance

    # DB에서 연결된 직무, 채용 공고, 그리고 회사 정보를 가져옴.
    job = prompt_instance.recruit_job
    recruitment = job.recruitment
    company = recruitment.company

    # 회사 정보 구성
    company_info = (
        f"회사명: {company.name}\n"
        f"산업: {company.industry}\n"
        f"비전: {company.vision}\n"
        f"미션: {company.mission}\n"
        f"핵심가치: {company.core_values}\n"
        f"최근 성과: {company.recent_achievements}\n"
        f"주요 이슈: {company.key_issues}"
    )

    # 직무 정보 구성
    job_info = (
        f"직무명: {job.title}\n"
        f"직무 설명: {job.description}\n"
        f"수행 업무: {job.key_roles}\n"
        f"필요한 기술: {job.required_skills}\n"
        f"관련 소프트 스킬: {job.soft_skills}\n"
        f"필요 강점: {job.related_technologies}"
    )

    # LLM에게 전달할 프롬프트 텍스트 구성
    prompt_text = f"""
    아래 정보를 바탕으로 자기소개서 답변 개요를 작성해줘. 단, 단순 요약이나 키워드 나열이 아닌, 다음 단계에 따라 논리적으로 사고하고 추론해서 구성해줘.

    [회사 정보]
    {company_info}

    [직무 정보]
    {job_info}

    [자기소개서 문항]
    {prompt_instance.question_text}

    ---

    각 문항에 대해 아래 단계를 따라 하나씩 생각하고 작성해줘:

    ### 1단계: 회사 인재상 분석
    - 회사 정보에서 드러나는 기업 가치, 조직 문화, 채용 시 중시하는 인재상 등을 추론해 정리해줘.
    - "이 회사가 중요하게 생각하는 역량/태도는 무엇인가?"에 대한 가설을 세워줘.

    ### 2단계: 직무 역량 도출
    - 직무 정보에서 해당 포지션에 필요한 핵심 역량, 기술, 역할을 분석해 정리해줘.
    - 이 직무에서 중요하게 작용할 수 있는 태도나 방식(예: 커뮤니케이션, 문제해결 방식 등)도 포함해줘.

    ### 3단계: 문항 의도 분석 및 핵심 주제 설정
    - 문항이 평가하고자 하는 역량이나 성향이 무엇인지 추론해줘.
    - 문항의 방향성에 맞춰 답변에서 강조해야 할 핵심 주제를 한 문장으로 요약해줘.

    ### 4단계: 키워드 선정
    - 위 단계들에서 도출한 정보들을 바탕으로, 이 문항에 포함할 키워드를 선정해줘.
    - 키워드는 회사 가치, 직무 역량, 경험 사례와 연결될 수 있어야 해.

    ### 5단계: 경험 사례 매칭
    - 지원자의 경험 중, 이 문항의 핵심 주제 및 키워드와 가장 잘 연결될 수 있는 하나의 사례를 선택해줘.
    - 사례는 회사와 직무가 요구하는 가치/역량과 연결되어야 하며, 다른 문항과 중복되지 않아야 해.
    - 선택한 경험에서 보여줄 수 있는 구체적인 행동과 결과를 간략히 요약해줘.

    ---

    주의사항:
    - 하나의 문항에는 하나의 주요 경험만 사용해.
    - 동일한 직무 내 다른 문항들과는 다른 경험과 역량을 반영하도록 구성해.
    - 각 단계마다 reasoning이 보이도록 작성해줘. 단순 나열이 아닌 “왜 그런 선택을 했는지”를 설명해줘.
    """

    # LLM 호출하여 개요 생성 후 저장
    outline = llm.predict(prompt_text)
    prompt_instance.outline = outline
    prompt_instance.save()
    print(f"[DEBUG] Generated and saved Cover Letter Outline for prompt id: {prompt_instance.id}")
    return prompt_instance
