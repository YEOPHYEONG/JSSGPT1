import os
import json
import pdfplumber
from django.shortcuts import render, redirect
from django.http import JsonResponse
from dotenv import load_dotenv  # 추가
from langchain_community.chat_models import ChatOpenAI  # 1번 코드와 동일하게 사용한다고 가정
# 또는 from langchain_openai import OpenAI
from django.contrib.auth.decorators import login_required
import logging

from .models import RawExperience, STARExperience
from .forms import ResumeUploadForm
from .utils import calculate_similarity
from .utils import parse_openai_response

# 로깅 설정
logger = logging.getLogger('django')

# .env 로드
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# (ChatOpenAI를 쓴다면) LLM 인스턴스 생성
# model, temperature는 1번 코드와 동일하게 조정 가능합니다.
llm = ChatOpenAI(
    model="gpt-4", 
    temperature=0, 
    openai_api_key=openai_api_key
)

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
                주어진 텍스트를 분석하여 STAR 구조 데이터를 JSON 배열 형식으로 반환하세요.
                각 항목은 다음 키를 포함해야 합니다:
                - "title": 경험의 제목을 한 문장으로 정리
                - "situation": 경험의 상황을 한 문장으로 정리
                - "task": 해결해야 할 과제를 한 문장으로 정리
                - "action": 수행한 행동을 한 문장으로 정리
                - "result": 결과을 한 문장으로 정리
                단, 경험의 상황, 해결해야 할 과제, 수행한 행동, 결과 중 정확히 파악할 수 없는 내용은 '경험을 입력해주세요'로 반환하세요.
                JSON 외의 응답을 포함하지 말고, 순수 JSON만 반환하세요.
                텍스트: {extracted_text}
                """
                
                # LangChain의 predict() 사용
                response_text = llm.predict(prompt)

                # OpenAI 응답 로깅
                logger.debug(f"OpenAI Response: {response_text}")

                # Step 4: OpenAI 응답 파싱
                try:
                    star_data = parse_openai_response(response_text)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON Decode Error: {e}")
                    return JsonResponse({
                        'error': 'Failed to parse JSON from OpenAI response.'
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
                # 에러 처리 및 로깅
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
            # user에 해당하는 RawExperience 가져오기 (없으면 생성)
            raw_experience, _ = RawExperience.objects.get_or_create(user=request.user)

            data = json.loads(request.body)  # { title, situation, task, action, result }
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

