import os
import json
import pdfplumber
from django.shortcuts import render, redirect
from django.http import JsonResponse
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from django.contrib.auth.decorators import login_required
import logging

from .models import RawExperience, STARExperience
from .forms import ResumeUploadForm
from .utils import calculate_similarity

# 로깅 설정
logger = logging.getLogger('django')

# .env 로드
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# LLM 인스턴스 생성 (ChatOpenAI 사용)
llm = ChatOpenAI(
    model="gpt-4o-2024-11-20",
    temperature=0.5,
    openai_api_key=openai_api_key
)

def parse_openai_response(response):
    """
    OpenAI 응답을 JSON 형태로 파싱합니다.
    JSON 형식이 아닐 경우, 텍스트를 파싱하여 딕셔너리 리스트로 변환.
    """
    # 응답에서 불필요한 태그 제거
    cleaned_response = response.strip().replace("```json", "").replace("```", "")
    
    try:
        # JSON 파싱 시도
        parsed_data = json.loads(cleaned_response)
        logger.debug(f"Successfully parsed JSON: {parsed_data}")
        return parsed_data
    except json.JSONDecodeError as e:
        logger.warning(f"OpenAI Response is not valid JSON: {e}. Attempting to parse manually.")
        # 수동 파싱 로직 (배열 처리 가능하도록 개선)
        parsed_data = []
        current_item = {}
        lines = cleaned_response.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("{"):
                current_item = {}
            elif line.startswith("}"):
                if current_item:
                    parsed_data.append(current_item)
                    current_item = {}
            elif ":" in line:
                key, value = line.split(":", 1)
                current_item[key.strip().strip('"')] = value.strip().strip('",')
        if current_item:  # 마지막 항목 추가
            parsed_data.append(current_item)
        logger.debug(f"Manually parsed data: {parsed_data}")
        return parsed_data

@login_required
def upload_resume(request):
    """
    이력서를 업로드하면 다음 작업 수행:
    1. PDF 텍스트 추출 후 RawExperience에 저장.
    2. OpenAI API 호출하여 STAR 구조 생성.
    3. 기존 STARExperience 데이터와 유사도 비교 후 저장 또는 업데이트.
    """
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Step 1: RawExperience 가져오기 또는 생성
                raw_experience, created = RawExperience.objects.get_or_create(user=request.user)

                # Step 2: PDF 파일 텍스트 추출
                uploaded_file = request.FILES['resume_file']
                with pdfplumber.open(uploaded_file) as pdf:
                    extracted_text = "".join(
                        [page.extract_text() or "" for page in pdf.pages]
                    )

                # RawExperience 데이터 업데이트
                raw_experience.extracted_text = extracted_text
                raw_experience.resume_file = uploaded_file
                raw_experience.save()
                logger.debug(f"Updated RawExperience: {raw_experience}")

                # Step 3: OpenAI GPT 호출
                prompt = f"""
                다음은 사용자의 이력서에서 추출한 텍스트야.

                텍스트: {extracted_text}

                너의 목표는, 이 텍스트에서 자기소개서 작성에 활용할 수 있는 경험들을 찾아, 설득력 있는 STAR 구조로 재구성하는 거야.  
                단순한 요약이 아니라, **자기소개서에 들어갈 수 있을 만큼 논리적이고 명확한 흐름을 가진 경험**이 되도록 해줘.

                각 경험을 STAR 구조로 정리하기 전에, 다음 기준에 따라 논리적으로 판단하고 구성해줘:

                ---

                ### [Reasoning 단계 안내]

                1. **경험 식별**  
                - 텍스트를 읽고, 하나의 명확한 사건이나 프로젝트, 역할 수행이 드러나는 단위를 "하나의 경험"으로 간주해.
                - 비슷한 활동이라도 주체가 다른 문제를 해결했다면 별개의 경험으로 나눠.

                2. **STAR 구성 판단 기준**
                - S(상황): 경험이 일어난 맥락, 배경, 조직, 관련된 사람이나 문제 상황이 명확해야 해.
                - T(과제): 그 상황에서 당사자가 수행해야 했던 **도전적이거나 목표 지향적인 과제**를 추론해. 단순한 업무 지시는 피하고, 스스로 해결해야 했던 문제에 집중해서 서술해.
                - A(행동): 당사자가 실제로 했던 행동을 구체적으로, **문제 해결 방식, 순서, 협업 여부, 판단의 근거** 등을 포함해서 최소 3문장으로 서술해.
                - R(결과): 결과는 측정 가능하거나, 성과로 인식될 수 있는 명확한 한 줄로 정리해. 단, 정보가 부족하면 "경험을 입력해주세요"로 처리해.

                3. **불완전한 정보 판단**
                - 위의 판단 기준에 따라, 정보가 부족하거나 명확하지 않으면 그 항목에는 `"경험을 입력해주세요"`를 넣어줘.

                ---

                ### [출력 형식]

                아래 형식의 **JSON 배열**로 반환해줘. JSON 외의 설명은 포함하지 마.

                ```json
                [
                {
                    "title": "경험의 제목",
                    "situation": "경험의 배경, 맥락 등을 최소 3문장으로 명확히 서술",
                    "task": "해결해야 했던 과제나 도전 과제",
                    "action": "당사자가 수행한 행동, 문제 해결 방식, 의사결정 등을 구체적으로 설명",
                    "result": "성과나 결과 한 문장. 불분명하면 '경험을 입력해주세요'"
                },
                ...
                ]
                """
                
                # OpenAI API 호출
                try:
                    logger.debug("Received response from OpenAI: start")
                    response_text = llm.predict(prompt)
                    logger.debug(f"Received response from OpenAI: {response_text}")
                except Exception as api_error:
                    logger.error(f"OpenAI API call error: {api_error}")
                    return JsonResponse({
                        'error': 'OpenAI API call failed. Please try again later.'
                    }, status=500)

                # Step 4: OpenAI 응답 파싱
                try:
                    logger.debug("Received response from OpenAI: parsing***")
                    star_data = parse_openai_response(response_text)
                    logger.debug(f"Parsed STAR Data: {star_data}")
                except Exception as e:
                    logger.error(f"Error parsing OpenAI response: {e}")
                    return JsonResponse({
                        'error': 'Failed to parse response from OpenAI.'
                    }, status=500)

                # STAR 데이터 각각 처리
                for item in star_data:
                    logger.debug(f"Processing STAR Data: {item}")

                    # 기존 STARExperience와 유사도 비교
                    existing_stars = STARExperience.objects.filter(user=request.user)
                    is_updated = False
                    for existing_star in existing_stars:
                        similarity = calculate_similarity(
                            existing_star.situation,
                            item.get('situation', "")
                        )
                        if similarity >= 0.7:
                            # 기존 데이터 업데이트
                            existing_star.title = item.get('title', "")
                            existing_star.situation = item.get('situation', "")
                            existing_star.task = item.get('task', "")
                            existing_star.action = item.get('action', "")
                            existing_star.result = item.get('result', "")
                            existing_star.save()
                            logger.debug(f"Updated STARExperience: {existing_star}")
                            is_updated = True
                            break

                    # 유사한 것이 없으면 새롭게 생성
                    if not is_updated:
                        new_star = STARExperience.objects.create(
                            user=request.user,
                            raw_experience=raw_experience,
                            title=item.get('title', ""),
                            situation=item.get('situation', ""),
                            task=item.get('task', ""),
                            action=item.get('action', ""),
                            result=item.get('result', "")
                        )
                        logger.debug(f"Created new STARExperience: {new_star}")

                return JsonResponse({
                    'message': 'Resume uploaded and STAR experiences processed successfully.'
                })
            except Exception as e:
                logger.error(f"Error during resume processing: {str(e)}")
                return JsonResponse({
                    'error': 'An error occurred during resume processing.'
                }, status=500)
    else:
        form = ResumeUploadForm()

    # GET 요청: 업로드 폼 렌더링
    return render(request, 'user_experience/upload_resume.html', {'form': form})

@login_required
def get_star_experiences(request):
    """
    현재 로그인된 사용자의 STARExperience 목록을 JSON으로 반환 (updated_at 내림차순)
    """
    star_exps = STARExperience.objects.filter(user=request.user).order_by('-updated_at')
    data = []
    for exp in star_exps:
        data.append({
            'id': exp.id,
            'title': exp.title,
            'situation': exp.situation,
            'task': exp.task,
            'action': exp.action,
            'result': exp.result
        })
    return JsonResponse(data, safe=False)

@login_required
def create_star_experience(request):
    """
    새로운 STARExperience를 빈 값으로 생성
    """
    if request.method == 'POST':
        try:
            raw_experience, _ = RawExperience.objects.get_or_create(user=request.user)
            data = json.loads(request.body)
            exp = STARExperience.objects.create(
                user=request.user,
                raw_experience=raw_experience,
                title=data.get('title', ''),
                situation=data.get('situation', ''),
                task=data.get('task', ''),
                action=data.get('action', ''),
                result=data.get('result', '')
            )
            return JsonResponse({
                'id': exp.id,
                'title': exp.title,
                'situation': exp.situation,
                'task': exp.task,
                'action': exp.action,
                'result': exp.result
            })
        except Exception as e:
            logger.error(f"Error creating new STARExperience: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid HTTP method.'}, status=405)

@login_required
def update_star_experience(request, star_id):
    """
    기존 STARExperience를 수정
    """
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            exp = STARExperience.objects.get(id=star_id, user=request.user)
            exp.title = data.get('title', exp.title)
            exp.situation = data.get('situation', exp.situation)
            exp.task = data.get('task', exp.task)
            exp.action = data.get('action', exp.action)
            exp.result = data.get('result', exp.result)
            exp.save()
            return JsonResponse({'message': 'STARExperience updated successfully.'})
        except STARExperience.DoesNotExist:
            return JsonResponse({'error': 'STARExperience not found.'}, status=404)
        except Exception as e:
            logger.error(f"Error updating STARExperience: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid HTTP method.'}, status=405)